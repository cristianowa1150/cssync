#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =====================================================================
#  CSSync — versão Linux (rsync)
#  Porte fiel do "CSSync" (Windows/PowerShell) de Cristiano Silveira Silva.
#  © 2026 Cristiano Silveira Silva — Licença CC BY 4.0
#  Faz o mesmo papel: monta o comando, mostra exatamente o que vai rodar
#  e executa o rsync (o "robocopy do Linux"). A pasta FONTE (A) nunca é alterada.
#
#  Requisitos: python3 + Tk + rsync
#     Fedora:  sudo dnf install -y rsync python3-tkinter
#     Debian:  sudo apt install -y rsync python3-tk
# =====================================================================

import os
import sys
import time
import shlex
import shutil
import queue
import threading
import subprocess

APP_VERSION = "1.6"
LOG_PATH = os.path.expanduser("~/cssync.log")

# ---------------------------------------------------------------------
# Opções do rsync mostradas na tela (equivalentes às do robocopy).
#   flag    -> token(s) passados ao rsync
#   show    -> rótulo curto exibido (opcional; padrão = flag)
#   checked -> marcado por padrão
#   danger  -> exibe em vermelho (operação destrutiva)
# ---------------------------------------------------------------------
def build_options():
    return [
        {"flag": "-r",                 "checked": True,  "desc": "Copia todas as subpastas, inclusive as vazias"},
        {"flag": "-t",                 "checked": True,  "desc": "Mantém a data e a hora dos arquivos copiados"},
        {"flag": "-p",                 "checked": True,  "desc": "Mantém as permissões dos arquivos"},
        {"flag": "-l",                 "checked": True,  "desc": "Copia links simbólicos como links (sem copiar o conteúdo apontado)"},
        {"flag": "--partial",          "checked": False, "desc": "Modo reiniciável: retoma a cópia de onde parou se for interrompida"},
        {"flag": "-u",                 "checked": False, "desc": "Protege o destino: se o arquivo em B for mais novo que em A, ele é mantido"},
        {"flag": "--modify-window=1",  "checked": False, "desc": "Tolerância de 1s na data (use com pendrive, rede ou FAT32/exFAT)"},
        {"flag": "-o",                 "checked": False, "desc": "Mantém o dono dos arquivos (abra o app com sudo)"},
        {"flag": "-g",                 "checked": False, "desc": "Mantém o grupo dos arquivos (abra o app com sudo)"},
        {"flag": "-A",                 "checked": False, "desc": "Mantém ACLs / permissões avançadas (abra o app com sudo)"},
        {"flag": "-X",                 "checked": False, "desc": "Mantém atributos estendidos (xattrs)"},
        {"flag": "-H",                 "checked": False, "desc": "Preserva hard links (vários nomes apontando para o mesmo conteúdo)"},
        {"flag": "-z",                 "checked": False, "desc": "Comprime durante a transferência (acelera em rede; em disco local não precisa)"},
        {"flag": "-c",                 "checked": False, "desc": "Compara pelo conteúdo, não só por data e tamanho (mais lento, mais rigoroso)"},
        {"flag": "--exclude=.*",       "checked": False, "desc": "Não copia arquivos e pastas ocultos (começados com ponto)"},
        {"flag": "--info=progress2",   "checked": True,  "desc": "Mostra o progresso e o percentual geral da cópia"},
        {"flag": "-v",                 "checked": False, "desc": "Modo detalhado: mostra cada arquivo processado"},
        {"flag": "--log-file=" + LOG_PATH, "show": "--log-file", "checked": False,
         "desc": "Salva um registro da cópia em cssync.log na sua pasta pessoal"},
        {"flag": "--delete",           "checked": False, "danger": True,
         "desc": "ESPELHAR: deixa B IDÊNTICO a A (APAGA de B tudo que não existe mais em A!)"},
    ]

# Flags base usadas pelos três botões de modo (equivale a /MT /R /W /XJ /DCOPY:DAT do robocopy)
BASE_FLAGS = ["-a", "--info=progress2", "--human-readable"]

# Cores do texto da janela de cópia (nome -> (fundo, fonte))
CORES = [
    ("Verde (estilo Linux)", "#000000", "#27d127"),
    ("Padrão (cinza claro)", "#000000", "#d0d0d0"),
    ("Branco brilhante",     "#000000", "#ffffff"),
    ("Amarelo",              "#000000", "#ffd400"),
    ("Ciano",                "#000000", "#23dede"),
    ("Vermelho claro",       "#000000", "#ff6b6b"),
    ("Magenta",              "#000000", "#ff5cff"),
    ("Preto sobre branco",   "#ffffff", "#000000"),
]

RETRYABLE = {10, 11, 12, 23, 24, 30, 35}


# ---------------------------------------------------------------------
# LÓGICA PURA (sem Tk — testável isoladamente)
# ---------------------------------------------------------------------
def format_path(p):
    p = (p or "").strip().strip('"').rstrip("/")
    return p


def split_lista(texto):
    return [x.strip().strip('"') for x in (texto or "").split(";") if x.strip()]


def build_command(flags, src, dst, excl_files="", excl_dirs=""):
    """Monta a lista de argumentos do rsync (origem -> destino)."""
    cmd = ["rsync"]
    cmd += list(flags)

    for f in split_lista(excl_files):
        cmd.append("--exclude=" + f)
    for d in split_lista(excl_dirs):
        if not d.endswith("/"):
            d += "/"
        cmd.append("--exclude=" + d)

    s = format_path(src)
    if s:
        s += "/"   # barra final => copia o CONTEÚDO da pasta (igual ao robocopy)
    t = format_path(dst)
    if t:
        t += "/"
    cmd.append(s)
    cmd.append(t)
    return cmd


def preview_string(cmd):
    return " ".join(shlex.quote(c) for c in cmd)


def install_hint():
    text = ""
    try:
        with open("/etc/os-release") as f:
            text = f.read().lower()
    except Exception:
        pass
    if "fedora" in text:
        return "sudo dnf install -y rsync python3-tkinter"
    if "debian" in text or "ubuntu" in text or "mint" in text:
        return "sudo apt update && sudo apt install -y rsync python3-tk"
    return "Instale os pacotes 'rsync' e o módulo Tk do Python pela sua distribuição."


# ---------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    TK_AVAILABLE = True
except Exception:
    TK_AVAILABLE = False


if TK_AVAILABLE:

    COR_ATUALIZAR = "#227846"
    COR_ESPELHAR  = "#c05416"
    COR_NOVOS     = "#1e5aa0"
    COR_SIMULAR   = "#643c96"
    COR_PERIGO    = "#b22222"

    class ConsoleWindow(tk.Toplevel):
        """Janela que mostra o comando e a saída ao vivo do rsync (com cor escolhida)."""
        def __init__(self, master, cmd, retries, wait, bg, fg, dry_run):
            super().__init__(master)
            self.title("Cópia em andamento — CSSync")
            self.geometry("900x560")
            self.cmd = cmd
            self.retries = retries
            self.wait = wait
            self.dry_run = dry_run
            self.proc = None
            self.stopped = False
            self.msg_queue = queue.Queue()

            self.text = tk.Text(self, wrap="word", bg=bg, fg=fg,
                                insertbackground=fg, font=("Monospace", 11))
            self.text.pack(fill="both", expand=True, padx=8, pady=(8, 4))

            bar = ttk.Frame(self)
            bar.pack(fill="x", padx=8, pady=(0, 8))
            self.btn_stop = ttk.Button(bar, text="Parar", command=self.stop)
            self.btn_stop.pack(side="left")
            self.btn_close = ttk.Button(bar, text="Fechar", command=self.destroy, state="disabled")
            self.btn_close.pack(side="right")

            self._write("=" * 70 + "\n")
            self._write(("SIMULAÇÃO (nada será copiado)\n" if dry_run else "EXECUTANDO\n"))
            self._write(preview_string(cmd) + "\n")
            self._write("=" * 70 + "\n\n")

            self.protocol("WM_DELETE_WINDOW", self._on_close_request)
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            self.after(100, self._poll)

        def _write(self, s):
            self.text.insert("end", s)
            self.text.see("end")

        def _worker(self):
            attempts = self.retries + 1
            for i in range(attempts):
                if self.stopped:
                    break
                try:
                    self.proc = subprocess.Popen(
                        self.cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        text=True, bufsize=1)
                except FileNotFoundError:
                    self.msg_queue.put("[ERRO] rsync não encontrado. Instale com:\n  " + install_hint() + "\n")
                    break
                except Exception as e:
                    self.msg_queue.put(f"[ERRO] não foi possível iniciar o rsync: {e}\n")
                    break

                for line in self.proc.stdout:
                    self.msg_queue.put(line)
                self.proc.wait()
                rc = self.proc.returncode
                self.proc = None

                if self.stopped:
                    self.msg_queue.put("\n[Interrompido pelo usuário]\n")
                    break
                if rc == 0:
                    self.msg_queue.put("\n===== Concluído com sucesso (código 0) =====\n")
                    break
                if self.dry_run:
                    self.msg_queue.put(f"\n===== Simulação concluída (código {rc}) =====\n")
                    break
                if rc in RETRYABLE and i < attempts - 1:
                    self.msg_queue.put(f"\n[Erro recuperável: código {rc}] nova tentativa em {self.wait}s...\n")
                    for _ in range(self.wait):
                        if self.stopped:
                            break
                        time.sleep(1)
                else:
                    self.msg_queue.put(f"\n===== Terminou com código {rc} — verifique as mensagens acima =====\n")
                    break
            self.msg_queue.put("__DONE__")

        def _poll(self):
            try:
                while True:
                    msg = self.msg_queue.get_nowait()
                    if msg == "__DONE__":
                        self.btn_stop.configure(state="disabled")
                        self.btn_close.configure(state="normal")
                    else:
                        self._write(msg)
            except queue.Empty:
                pass
            if self.winfo_exists():
                self.after(100, self._poll)

        def stop(self):
            self.stopped = True
            if self.proc is not None:
                try:
                    self.proc.terminate()
                except Exception:
                    pass

        def _on_close_request(self):
            if self.proc is not None:
                if not messagebox.askyesno("CSSync",
                                           "A cópia ainda está rodando. Parar e fechar?"):
                    return
                self.stop()
            self.destroy()

    class CSSyncApp(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title("CSSync  —  copiar FONTE (A)  →  DESTINO (B)")
            self.geometry("960x860")
            self.minsize(900, 760)

            self.v_src = tk.StringVar()
            self.v_dst = tk.StringVar()
            self.v_xf = tk.StringVar()
            self.v_xd = tk.StringVar()
            self.v_cor = tk.StringVar(value=CORES[0][0])
            self.v_delta = tk.BooleanVar(value=False)

            self.options = build_options()
            self.opt_vars = []

            self._build_ui()
            self._check_rsync()
            self._update_preview()

        # ---------------- Interface ----------------
        def _build_ui(self):
            bold = ("Sans", 11, "bold")

            self.banner = tk.Label(self, text="", fg="white", bg=COR_PERIGO, anchor="w")

            # ----- FONTE (A) -----
            f1 = ttk.Frame(self); f1.pack(fill="x", padx=12, pady=(10, 0))
            tk.Label(f1, text="Pasta FONTE (A) — de onde os arquivos vêm:", font=bold).pack(anchor="w")
            r1 = ttk.Frame(f1); r1.pack(fill="x", pady=(2, 0))
            ttk.Entry(r1, textvariable=self.v_src).pack(side="left", fill="x", expand=True)
            ttk.Button(r1, text="Procurar...", command=self.pick_src).pack(side="left", padx=(8, 0))

            # ----- DESTINO (B) -----
            f2 = ttk.Frame(self); f2.pack(fill="x", padx=12, pady=(8, 0))
            tk.Label(f2, text="Pasta DESTINO (B) — para onde os arquivos vão (criada se não existir):",
                     font=bold).pack(anchor="w")
            r2 = ttk.Frame(f2); r2.pack(fill="x", pady=(2, 0))
            ttk.Entry(r2, textvariable=self.v_dst).pack(side="left", fill="x", expand=True)
            ttk.Button(r2, text="Procurar...", command=self.pick_dst).pack(side="left", padx=(8, 0))

            # ----- Opções (com rolagem) -----
            grp = ttk.LabelFrame(self, text=" Opções do rsync — role a lista para ver todas ")
            grp.pack(fill="x", padx=12, pady=(10, 0))
            canvas = tk.Canvas(grp, height=232, highlightthickness=0)
            sb = ttk.Scrollbar(grp, orient="vertical", command=canvas.yview)
            inner = ttk.Frame(canvas)
            inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=inner, anchor="nw")
            canvas.configure(yscrollcommand=sb.set)
            canvas.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=6)
            sb.pack(side="right", fill="y", pady=6)

            def _wheel(ev):
                canvas.yview_scroll(int(-1 * (ev.delta / 120)) if ev.delta else 0, "units")
            def _wheel_lin(ev):
                canvas.yview_scroll(-1 if ev.num == 4 else 1, "units")
            canvas.bind_all("<MouseWheel>", _wheel)
            canvas.bind_all("<Button-4>", _wheel_lin)
            canvas.bind_all("<Button-5>", _wheel_lin)

            for op in self.options:
                var = tk.BooleanVar(value=op["checked"])
                self.opt_vars.append(var)
                show = op.get("show", op["flag"])
                cb = tk.Checkbutton(inner, variable=var,
                                    text=f"{show}   —   {op['desc']}",
                                    anchor="w", justify="left",
                                    font=("Sans", 11),
                                    command=self._update_preview)
                if op.get("danger"):
                    cb.configure(fg=COR_PERIGO)
                cb.pack(fill="x", anchor="w", padx=4, pady=2)

            # ----- Exclusões -----
            f3 = ttk.Frame(self); f3.pack(fill="x", padx=12, pady=(10, 0))
            tk.Label(f3, text="Excluir arquivos:").grid(row=0, column=0, sticky="w")
            e_xf = ttk.Entry(f3, textvariable=self.v_xf, width=30)
            e_xf.grid(row=0, column=1, sticky="w", padx=(6, 24))
            tk.Label(f3, text="Excluir pastas:").grid(row=0, column=2, sticky="w")
            e_xd = ttk.Entry(f3, textvariable=self.v_xd, width=30)
            e_xd.grid(row=0, column=3, sticky="w", padx=(6, 0))
            tk.Label(self, text="Separe por ponto e vírgula.  Ex.: *.tmp; *.bak   |   Pastas: node_modules; .git",
                     fg="#666666").pack(anchor="w", padx=12)

            # ----- Pré-visualização + cor -----
            f4 = ttk.Frame(self); f4.pack(fill="x", padx=12, pady=(8, 0))
            tk.Label(f4, text="Comando que será executado:", font=bold).pack(side="left")
            tk.Label(f4, text="Cor do texto da cópia:").pack(side="left", padx=(24, 6))
            cmb = ttk.Combobox(f4, textvariable=self.v_cor, state="readonly",
                               values=[c[0] for c in CORES], width=24)
            cmb.pack(side="left")

            self.preview = tk.Text(self, height=3, wrap="word", font=("Monospace", 10),
                                   bg="#0f172a", fg="#e2e8f0")
            self.preview.pack(fill="x", padx=12, pady=(4, 0))
            self.preview.configure(state="disabled")

            # ----- Cópia delta (diferencial do Linux/rsync) — vale para todos os modos -----
            tk.Checkbutton(
                self, variable=self.v_delta, anchor="w", justify="left", fg=COR_ATUALIZAR,
                font=("Sans", 11, "bold"), command=self._update_preview,
                text="⚡ Cópia delta (rsync): envia só as PARTES que mudaram de cada arquivo — "
                     "excelente para arquivos grandes (bancos de dados, VMs, vídeos, PSTs)"
            ).pack(fill="x", padx=12, pady=(6, 0))

            # ----- Botões de modo -----
            self.btn_atualizar = tk.Button(
                self, text="▶  ATUALIZAR BACKUP (A → B) — copia NOVOS e ALTERADOS, não apaga nada em B",
                bg=COR_ATUALIZAR, fg="white", activebackground=COR_ATUALIZAR, activeforeground="white",
                relief="flat", font=("Sans", 12, "bold"), pady=10, command=self.run_atualizar)
            self.btn_atualizar.pack(fill="x", padx=12, pady=(10, 0))

            self.btn_espelhar = tk.Button(
                self, text="⟳  ESPELHAR (A → B) — B fica IDÊNTICO a A (apaga de B o que não existe em A)",
                bg=COR_ESPELHAR, fg="white", activebackground=COR_ESPELHAR, activeforeground="white",
                relief="flat", font=("Sans", 11, "bold"), pady=9, command=self.run_espelhar)
            self.btn_espelhar.pack(fill="x", padx=12, pady=(8, 0))

            # ----- Botões secundários -----
            f5 = ttk.Frame(self); f5.pack(fill="x", padx=12, pady=(10, 6))
            ttk.Button(f5, text="Executar opções marcadas", command=self.run_marcadas).pack(side="left")
            tk.Button(f5, text="Simular — não copia", fg=COR_SIMULAR, command=self.run_simular).pack(side="left", padx=8)
            tk.Button(f5, text="Só arquivos NOVOS em B", fg=COR_NOVOS, command=self.run_novos).pack(side="left")
            tk.Button(f5, text="?  Ajuda", fg=COR_NOVOS, font=("Sans", 11, "bold"),
                      command=self.show_help).pack(side="right")

            # ----- Rodapé -----
            tk.Label(self, fg="#666666",
                     text=f"v{APP_VERSION} (Linux/rsync) — © 2026 Cristiano Silveira Silva — CC BY 4.0   |   "
                          "rsync: código 0 = sucesso; diferente de 0 = verifique as mensagens.")\
                .pack(anchor="w", padx=12, pady=(0, 8))

            # Atualiza a prévia ao digitar
            for v in (self.v_src, self.v_dst, self.v_xf, self.v_xd):
                v.trace_add("write", lambda *a: self._update_preview())

        # ---------------- Helpers ----------------
        def pick_src(self):
            d = filedialog.askdirectory(title="Escolha a pasta FONTE (A)")
            if d:
                self.v_src.set(d)

        def pick_dst(self):
            d = filedialog.askdirectory(title="Escolha a pasta DESTINO (B)")
            if d:
                self.v_dst.set(d)

        def get_checked_flags(self):
            flags = []
            for op, var in zip(self.options, self.opt_vars):
                if var.get():
                    flags.append(op["flag"])
            return flags

        def delta_flags(self):
            # --no-whole-file força o algoritmo delta do rsync mesmo em cópia local
            return ["--no-whole-file"] if self.v_delta.get() else []

        def cor_atual(self):
            for nome, bg, fg in CORES:
                if nome == self.v_cor.get():
                    return bg, fg
            return CORES[0][1], CORES[0][2]

        def _update_preview(self):
            flags = self.get_checked_flags() + self.delta_flags()
            cmd = build_command(flags, self.v_src.get(),
                                self.v_dst.get(), self.v_xf.get(), self.v_xd.get())
            self.preview.configure(state="normal")
            self.preview.delete("1.0", "end")
            self.preview.insert("1.0", preview_string(cmd))
            self.preview.configure(state="disabled")

        def _check_rsync(self):
            if not shutil.which("rsync"):
                self.banner.configure(text="  rsync não encontrado. Instale com:  " + install_hint())
                self.banner.pack(fill="x", side="top")

        # ---------------- Execução ----------------
        def _executar(self, flags, dry_run=False):
            src = format_path(self.v_src.get())
            dst = format_path(self.v_dst.get())
            if not src or not dst:
                messagebox.showwarning("CSSync", "Informe a pasta FONTE e a pasta DESTINO.")
                return
            if not os.path.isdir(src):
                messagebox.showwarning("CSSync", f"A pasta FONTE não existe:\n{src}")
                return
            if os.path.abspath(src) == os.path.abspath(dst):
                messagebox.showwarning("CSSync", "A FONTE e o DESTINO são a mesma pasta.")
                return
            if not shutil.which("rsync"):
                messagebox.showerror("CSSync", "rsync não encontrado.\n\nInstale com:\n" + install_hint())
                return

            flags = list(flags) + self.delta_flags()
            cmd = build_command(flags, self.v_src.get(), self.v_dst.get(),
                                self.v_xf.get(), self.v_xd.get())
            self.preview.configure(state="normal")
            self.preview.delete("1.0", "end")
            self.preview.insert("1.0", preview_string(cmd))
            self.preview.configure(state="disabled")

            if (not dry_run) and ("--delete" in flags):
                if not messagebox.askyesno(
                    "Confirmar espelhamento",
                    "ATENÇÃO — modo ESPELHAR:\n\n"
                    "Tudo que existir no DESTINO (B) e não existir na FONTE (A) será APAGADO.\n\n"
                    "Dica: rode 'Simular' antes para conferir.\n\nDeseja continuar?"):
                    return

            bg, fg = self.cor_atual()
            ConsoleWindow(self, cmd, retries=1, wait=2, bg=bg, fg=fg, dry_run=dry_run)

        def run_atualizar(self):
            self._executar(list(BASE_FLAGS))

        def run_espelhar(self):
            self._executar(list(BASE_FLAGS) + ["--delete"])

        def run_novos(self):
            self._executar(list(BASE_FLAGS) + ["--ignore-existing"])

        def run_marcadas(self):
            self._executar(self.get_checked_flags())

        def run_simular(self):
            flags = self.get_checked_flags()
            if "-n" not in flags:
                flags = flags + ["-n"]
            self._executar(flags, dry_run=True)

        # ---------------- Ajuda ----------------
        def show_help(self):
            win = tk.Toplevel(self)
            win.title("Ajuda — CSSync")
            win.geometry("860x680")
            txt = tk.Text(win, wrap="word", bg="white", relief="flat",
                          font=("Sans", 11), padx=16, pady=12)
            txt.pack(fill="both", expand=True)

            def add(s, color="#282828", bold=False, size=11):
                txt.tag_configure(f"t{len(txt.tag_names())}",
                                  foreground=color,
                                  font=("Sans", size, "bold" if bold else "normal"))
                txt.insert("end", s, txt.tag_names()[-1])

            add("OS 3 MODOS DE CÓPIA\n\n", "#282828", True, 15)

            add("ATUALIZAR BACKUP (A → B)   ", COR_ATUALIZAR, True, 13)
            add("— o botão do dia a dia\n", "#777777")
            add("Copia arquivos NOVOS e ALTERADOS de A para B (compara data e tamanho) e pula os idênticos.\n"
                "NÃO apaga nada em B: mesmo que você apague algo em A por engano, o backup continua em B.\n\n")

            add("ESPELHAR (A → B)   ", COR_ESPELHAR, True, 13)
            add("— use com atenção\n", "#777777")
            add("B fica IDÊNTICO a A: copia novos e alterados E TAMBÉM ")
            add("APAGA de B tudo que não existe mais em A. ", COR_PERIGO, True)
            add("\nSempre pede confirmação antes de executar.\n\n")

            add("SÓ ARQUIVOS NOVOS EM B   ", COR_NOVOS, True, 13)
            add("— não toca no que já existe\n", "#777777")
            add("Copia apenas o que NÃO existe em B. Não atualiza arquivos alterados e não apaga nada.\n"
                "Útil quando você quer ter certeza de que nada que já está em B será modificado.\n\n")

            add("SIMULAR — 100% seguro\n", COR_SIMULAR, True, 13)
            add("Apenas LISTA o que seria copiado ou apagado, sem fazer nada de verdade.\n"
                "Não copia, não altera e não apaga nenhum arquivo — nem em A, nem em B.\n"
                "Recomendado: simule antes do primeiro espelhamento para conferir o que será feito.\n\n")

            add("⚡ CÓPIA DELTA — diferencial do Linux\n", COR_ATUALIZAR, True, 13)
            add("Marque 'Cópia delta' para o rsync enviar APENAS as partes que mudaram de cada arquivo,\n"
                "em vez de recopiar o arquivo inteiro. Faz enorme diferença em arquivos grandes que mudam\n"
                "pouco — bancos de dados, máquinas virtuais, vídeos, arquivos PST. Vale para todos os modos.\n"
                "Tecnicamente força o algoritmo delta (--no-whole-file) mesmo em cópia local — algo que o\n"
                "robocopy do Windows não faz.\n\n")

            add("CÓDIGO DE SAÍDA (mostrado no fim da cópia)\n", "#282828", True, 13)
            add("0 = tudo certo.   ")
            add("diferente de 0 = algum arquivo não pôde ser copiado", COR_PERIGO, True)
            add(" (veja as mensagens na janela da cópia).\n\n")

            add("DICAS\n", "#282828", True, 13)
            add("• Pendrive ou HD externo em FAT32/exFAT: marque 'Tolerância de 1s na data' para evitar recópias.\n"
                "• Arquivos negando acesso (donos/permissões): abra o app com sudo e marque dono, grupo e ACLs.\n"
                "• Quer um registro do que foi copiado: marque '--log-file' (gera cssync.log na sua pasta).\n"
                "• A cor escolhida em 'Cor do texto da cópia' vale para toda a janela de console da cópia.\n\n")

            add(f"CSSync v{APP_VERSION} (Linux/rsync) — © 2026 Cristiano Silveira Silva — CC BY 4.0\n",
                "#777777", False, 10)

            txt.configure(state="disabled")
            ttk.Button(win, text="Fechar", command=win.destroy).pack(pady=(0, 10))


def main():
    if not TK_AVAILABLE:
        print("Tkinter não está instalado.\nInstale com:\n  " + install_hint())
        sys.exit(1)
    if not shutil.which("rsync"):
        print("Aviso: rsync não encontrado. O app abre, mas instale com:\n  " + install_hint())
    app = CSSyncApp()
    app.mainloop()


if __name__ == "__main__":
    main()

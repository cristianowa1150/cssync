#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =====================================================================
#  CSSync — versão Linux nativa (Qt / PySide6)
#  Porte do "CSSync" (Windows/PowerShell) de Cristiano Silveira Silva.
#  © 2026 Cristiano Silveira Silva — Licença CC BY 4.0
#  Usa o rsync por baixo (o "robocopy do Linux"). A pasta FONTE (A) nunca é alterada.
#
#  Requisitos: python3 + PySide6 + rsync
#     Fedora:  sudo dnf install -y rsync python3-pyside6
#     Debian:  sudo apt install -y rsync python3-pyside6.qtwidgets   (Debian 13+)
# =====================================================================

import os
import re
import sys
import shlex
import shutil

APP_VERSION = "1.6"
LOG_PATH = os.path.expanduser("~/cssync.log")


# ---------------------------------------------------------------------
# Opções do rsync mostradas na tela (equivalentes às do robocopy)
# ---------------------------------------------------------------------
def build_options():
    return [
        {"flag": "-r",                "checked": True,  "desc": "Copia todas as subpastas, inclusive as vazias"},
        {"flag": "-t",                "checked": True,  "desc": "Mantém a data e a hora dos arquivos copiados"},
        {"flag": "-p",                "checked": True,  "desc": "Mantém as permissões dos arquivos"},
        {"flag": "-l",                "checked": True,  "desc": "Copia links simbólicos como links (sem copiar o conteúdo apontado)"},
        {"flag": "--partial",         "checked": False, "desc": "Modo reiniciável: retoma a cópia de onde parou se for interrompida"},
        {"flag": "-u",                "checked": False, "desc": "Protege o destino: se o arquivo em B for mais novo que em A, ele é mantido"},
        {"flag": "--modify-window=1", "checked": False, "desc": "Tolerância de 1s na data (use com pendrive, rede ou FAT32/exFAT)"},
        {"flag": "-o",                "checked": False, "desc": "Mantém o dono dos arquivos (abra o app com sudo)"},
        {"flag": "-g",                "checked": False, "desc": "Mantém o grupo dos arquivos (abra o app com sudo)"},
        {"flag": "-A",                "checked": False, "desc": "Mantém ACLs / permissões avançadas (abra o app com sudo)"},
        {"flag": "-X",                "checked": False, "desc": "Mantém atributos estendidos (xattrs)"},
        {"flag": "-H",                "checked": False, "desc": "Preserva hard links (vários nomes apontando para o mesmo conteúdo)"},
        {"flag": "-z",                "checked": False, "desc": "Comprime durante a transferência (acelera em rede; em disco local não precisa)"},
        {"flag": "-c",                "checked": False, "desc": "Compara pelo conteúdo, não só por data e tamanho (mais lento, mais rigoroso)"},
        {"flag": "--exclude=.*",      "checked": False, "desc": "Não copia arquivos e pastas ocultos (começados com ponto)"},
        {"flag": "--info=progress2",  "checked": True,  "desc": "Mostra o progresso e o percentual geral da cópia"},
        {"flag": "-v",                "checked": False, "desc": "Modo detalhado: mostra cada arquivo processado"},
        {"flag": "--log-file=" + LOG_PATH, "show": "--log-file", "checked": False,
         "desc": "Salva um registro da cópia em cssync.log na sua pasta pessoal"},
        {"flag": "--delete",          "checked": False, "danger": True,
         "desc": "ESPELHAR: deixa B IDÊNTICO a A (APAGA de B tudo que não existe mais em A!)"},
    ]

# Flags base usadas pelos três botões de modo
BASE_FLAGS = ["-a", "--info=progress2", "--human-readable"]

# Cor do texto da janela de cópia (nome -> (fundo, fonte))
CORES = [
    ("Verde (estilo Linux)", "#000000", "#27d127"),
    ("Padrão (cinza claro)", "#101010", "#d0d0d0"),
    ("Branco brilhante",     "#000000", "#ffffff"),
    ("Amarelo",              "#000000", "#ffd400"),
    ("Ciano",                "#000000", "#23dede"),
    ("Vermelho claro",       "#000000", "#ff6b6b"),
    ("Magenta",              "#000000", "#ff5cff"),
    ("Preto sobre branco",   "#ffffff", "#000000"),
]

RETRYABLE = {10, 11, 12, 23, 24, 30, 35}

COR_ATUALIZAR = "#227846"
COR_ESPELHAR  = "#c05416"
COR_NOVOS     = "#1e5aa0"
COR_SIMULAR   = "#643c96"
COR_PERIGO    = "#b22222"


# ---------------------------------------------------------------------
# LÓGICA PURA (sem Qt — testável isoladamente)
# ---------------------------------------------------------------------
def format_path(p):
    return (p or "").strip().strip('"').rstrip("/")


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
        return "sudo dnf install -y rsync python3-pyside6"
    if "debian" in text or "ubuntu" in text or "mint" in text:
        return "sudo apt install -y rsync python3-pyside6.qtwidgets"
    return "Instale 'rsync' e o PySide6 (Qt) pela sua distribuição."


# ---------------------------------------------------------------------
# GUI (Qt / PySide6)
# ---------------------------------------------------------------------
try:
    from PySide6.QtWidgets import (
        QApplication, QWidget, QDialog, QLabel, QLineEdit, QPushButton,
        QCheckBox, QGroupBox, QScrollArea, QComboBox, QPlainTextEdit,
        QVBoxLayout, QHBoxLayout, QGridLayout, QFileDialog, QMessageBox,
        QSizePolicy, QFrame,
    )
    from PySide6.QtCore import Qt, QProcess, QTimer
    from PySide6.QtGui import QFont, QTextCursor, QIcon
    QT_AVAILABLE = True
except Exception:
    QT_AVAILABLE = False


if QT_AVAILABLE:

    ICON_PATH = "/usr/share/icons/hicolor/scalable/apps/cssync.svg"

    class ConsoleDialog(QDialog):
        """Janela que mostra o comando e a saída ao vivo do rsync (cor escolhida)."""
        def __init__(self, parent, cmd, retries, wait, bg, fg, dry_run):
            super().__init__(parent)
            self.setWindowTitle("Cópia em andamento — CSSync")
            self.resize(900, 560)
            self.cmd = cmd
            self.max_attempts = retries + 1
            self.attempt = 0
            self.wait = wait
            self.dry_run = dry_run
            self.stopped = False
            self.proc = None

            lay = QVBoxLayout(self)
            self.out = QPlainTextEdit()
            self.out.setReadOnly(True)
            self.out.setStyleSheet(
                f"QPlainTextEdit{{background-color:{bg};color:{fg};}}")
            self.out.setFont(QFont("Monospace", 11))
            self.out.setMaximumBlockCount(0)
            lay.addWidget(self.out, 1)

            bar = QHBoxLayout()
            self.btn_stop = QPushButton("Parar")
            self.btn_stop.clicked.connect(self.stop)
            self.btn_close = QPushButton("Fechar")
            self.btn_close.setEnabled(False)
            self.btn_close.clicked.connect(self.accept)
            bar.addWidget(self.btn_stop)
            bar.addStretch(1)
            bar.addWidget(self.btn_close)
            lay.addLayout(bar)

            self._append("=" * 70 + "\n")
            self._append("SIMULAÇÃO (nada será copiado)\n" if dry_run else "EXECUTANDO\n")
            self._append(preview_string(cmd) + "\n")
            self._append("=" * 70 + "\n\n")

            QTimer.singleShot(0, self._start)

        # ---- saída estilo terminal (trata \r como sobrescrever a linha) ----
        def _append(self, text):
            cur = self.out.textCursor()
            cur.movePosition(QTextCursor.End)
            for tok in re.split(r'(\r\n|\r|\n)', text):
                if tok == "":
                    continue
                if tok in ("\r\n", "\n"):
                    cur.insertText("\n")
                elif tok == "\r":
                    cur.movePosition(QTextCursor.StartOfBlock, QTextCursor.MoveAnchor)
                    cur.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
                    cur.removeSelectedText()
                else:
                    cur.insertText(tok)
            self.out.setTextCursor(cur)
            self.out.ensureCursorVisible()

        def _start(self):
            self.attempt += 1
            self.proc = QProcess(self)
            self.proc.setProcessChannelMode(QProcess.MergedChannels)
            self.proc.readyReadStandardOutput.connect(self._on_output)
            self.proc.finished.connect(self._on_finished)
            self.proc.errorOccurred.connect(self._on_error)
            self.proc.start(self.cmd[0], self.cmd[1:])

        def _on_output(self):
            data = bytes(self.proc.readAllStandardOutput()).decode("utf-8", "replace")
            self._append(data)

        def _on_error(self, err):
            if err == QProcess.FailedToStart:
                self._append("\n[ERRO] não foi possível iniciar o rsync. Instale com:\n  "
                             + install_hint() + "\n")
                self._finish()

        def _on_finished(self, code, status):
            if self.stopped:
                self._append("\n[Interrompido pelo usuário]\n")
                self._finish()
                return
            if code == 0:
                self._append("\n===== Concluído com sucesso (código 0) =====\n")
                self._finish()
            elif self.dry_run:
                self._append(f"\n===== Simulação concluída (código {code}) =====\n")
                self._finish()
            elif code in RETRYABLE and self.attempt < self.max_attempts:
                self._append(f"\n[Erro recuperável: código {code}] nova tentativa em {self.wait}s...\n")
                QTimer.singleShot(self.wait * 1000, self._start)
            else:
                self._append(f"\n===== Terminou com código {code} — verifique as mensagens acima =====\n")
                self._finish()

        def _finish(self):
            self.btn_stop.setEnabled(False)
            self.btn_close.setEnabled(True)

        def stop(self):
            self.stopped = True
            if self.proc is not None:
                self.proc.kill()

        def closeEvent(self, ev):
            if self.proc is not None and self.proc.state() != QProcess.NotRunning:
                r = QMessageBox.question(self, "CSSync",
                                         "A cópia ainda está rodando. Parar e fechar?")
                if r != QMessageBox.Yes:
                    ev.ignore()
                    return
                self.stop()
            ev.accept()

    class CSSyncWindow(QWidget):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("CSSync  —  copiar FONTE (A)  →  DESTINO (B)")
            self.resize(980, 880)
            if os.path.exists(ICON_PATH):
                self.setWindowIcon(QIcon(ICON_PATH))

            self.options = build_options()
            self.checks = []
            self._build_ui()
            self._check_rsync()
            self._update_preview()

        def _bold(self, text):
            lbl = QLabel(text)
            f = lbl.font(); f.setBold(True); lbl.setFont(f)
            return lbl

        def _build_ui(self):
            root = QVBoxLayout(self)
            root.setSpacing(6)

            self.banner = QLabel("")
            self.banner.setStyleSheet("background:#b22222;color:white;padding:6px;")
            self.banner.setVisible(False)
            root.addWidget(self.banner)

            # FONTE (A)
            root.addWidget(self._bold("Pasta FONTE (A) — de onde os arquivos vêm:"))
            r1 = QHBoxLayout()
            self.ed_src = QLineEdit()
            b1 = QPushButton("Procurar...")
            b1.clicked.connect(self.pick_src)
            r1.addWidget(self.ed_src, 1); r1.addWidget(b1)
            root.addLayout(r1)

            # DESTINO (B)
            root.addWidget(self._bold("Pasta DESTINO (B) — para onde os arquivos vão (criada se não existir):"))
            r2 = QHBoxLayout()
            self.ed_dst = QLineEdit()
            b2 = QPushButton("Procurar...")
            b2.clicked.connect(self.pick_dst)
            r2.addWidget(self.ed_dst, 1); r2.addWidget(b2)
            root.addLayout(r2)

            # Opções (rolagem)
            grp = QGroupBox(" Opções do rsync — role a lista para ver todas ")
            gl = QVBoxLayout(grp)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setMinimumHeight(230)
            scroll.setMaximumHeight(250)
            content = QWidget()
            cl = QVBoxLayout(content)
            cl.setSpacing(2)
            for op in self.options:
                show = op.get("show", op["flag"])
                cb = QCheckBox(f"{show}   —   {op['desc']}")
                cb.setChecked(op["checked"])
                f = cb.font(); f.setPointSize(11); cb.setFont(f)
                if op.get("danger"):
                    cb.setStyleSheet(f"color:{COR_PERIGO};")
                cb.toggled.connect(self._update_preview)
                cl.addWidget(cb)
                self.checks.append(cb)
            cl.addStretch(1)
            scroll.setWidget(content)
            gl.addWidget(scroll)
            root.addWidget(grp)

            # Exclusões
            ex = QGridLayout()
            ex.addWidget(QLabel("Excluir arquivos:"), 0, 0)
            self.ed_xf = QLineEdit(); self.ed_xf.setPlaceholderText("*.tmp; *.bak")
            ex.addWidget(self.ed_xf, 0, 1)
            ex.addWidget(QLabel("Excluir pastas:"), 0, 2)
            self.ed_xd = QLineEdit(); self.ed_xd.setPlaceholderText("node_modules; .git")
            ex.addWidget(self.ed_xd, 0, 3)
            ex.setColumnStretch(1, 1); ex.setColumnStretch(3, 1)
            root.addLayout(ex)
            hint = QLabel("Separe por ponto e vírgula.  Ex.: *.tmp; *.bak   |   Pastas: node_modules; .git")
            hint.setStyleSheet("color:gray;")
            root.addWidget(hint)

            # Pré-visualização + cor
            pr = QHBoxLayout()
            pr.addWidget(self._bold("Comando que será executado:"))
            pr.addStretch(1)
            pr.addWidget(QLabel("Cor do texto da cópia:"))
            self.cmb_cor = QComboBox()
            for nome, _bg, _fg in CORES:
                self.cmb_cor.addItem(nome)
            pr.addWidget(self.cmb_cor)
            root.addLayout(pr)

            self.preview = QPlainTextEdit()
            self.preview.setReadOnly(True)
            self.preview.setFixedHeight(70)
            self.preview.setFont(QFont("Monospace", 10))
            self.preview.setStyleSheet("QPlainTextEdit{background:#0f172a;color:#e2e8f0;}")
            root.addWidget(self.preview)

            # Cópia delta (diferencial do Linux/rsync) — aplica-se a TODOS os modos
            self.chk_delta = QCheckBox(
                "⚡ Cópia delta (rsync): envia só as PARTES que mudaram de cada arquivo — "
                "excelente para arquivos grandes (bancos de dados, VMs, vídeos, PSTs)")
            self.chk_delta.setStyleSheet(f"color:{COR_ATUALIZAR};font-weight:bold;")
            self.chk_delta.setToolTip(
                "Força o algoritmo delta do rsync (--no-whole-file) mesmo em cópia local.\n"
                "Em vez de recopiar o arquivo inteiro quando ele muda, transfere apenas os\n"
                "blocos alterados. Vale para os 3 modos, o Executar marcadas e o Simular.")
            self.chk_delta.toggled.connect(self._update_preview)
            root.addWidget(self.chk_delta)

            # Botões de modo
            self.btn_atualizar = QPushButton(
                "▶  ATUALIZAR BACKUP (A → B) — copia NOVOS e ALTERADOS, não apaga nada em B")
            self.btn_atualizar.setMinimumHeight(48)
            self.btn_atualizar.setStyleSheet(self._mode_style(COR_ATUALIZAR))
            self.btn_atualizar.clicked.connect(self.run_atualizar)
            root.addWidget(self.btn_atualizar)

            self.btn_espelhar = QPushButton(
                "⟳  ESPELHAR (A → B) — B fica IDÊNTICO a A (apaga de B o que não existe em A)")
            self.btn_espelhar.setMinimumHeight(44)
            self.btn_espelhar.setStyleSheet(self._mode_style(COR_ESPELHAR))
            self.btn_espelhar.clicked.connect(self.run_espelhar)
            root.addWidget(self.btn_espelhar)

            # Botões secundários
            sec = QHBoxLayout()
            b_exec = QPushButton("Executar opções marcadas")
            b_exec.clicked.connect(self.run_marcadas)
            b_sim = QPushButton("Simular — não copia")
            b_sim.setStyleSheet(f"color:{COR_SIMULAR};font-weight:bold;")
            b_sim.clicked.connect(self.run_simular)
            b_novos = QPushButton("Só arquivos NOVOS em B")
            b_novos.setStyleSheet(f"color:{COR_NOVOS};")
            b_novos.clicked.connect(self.run_novos)
            b_ajuda = QPushButton("?  Ajuda")
            b_ajuda.setStyleSheet(f"color:{COR_NOVOS};font-weight:bold;")
            b_ajuda.clicked.connect(self.show_help)
            sec.addWidget(b_exec); sec.addWidget(b_sim); sec.addWidget(b_novos)
            sec.addStretch(1); sec.addWidget(b_ajuda)
            root.addLayout(sec)

            # Rodapé
            foot = QLabel(f"v{APP_VERSION} (Linux/Qt · rsync) — © 2026 Cristiano Silveira Silva — "
                          "CC BY 4.0   |   rsync: código 0 = sucesso; diferente de 0 = verifique.")
            foot.setStyleSheet("color:gray;")
            root.addWidget(foot)

            # Atualiza a prévia ao digitar
            for ed in (self.ed_src, self.ed_dst, self.ed_xf, self.ed_xd):
                ed.textChanged.connect(self._update_preview)

        def _mode_style(self, color):
            return (f"QPushButton{{background-color:{color};color:white;font-weight:bold;"
                    f"border:none;border-radius:5px;padding:8px;}}"
                    f"QPushButton:hover{{background-color:{color};}}"
                    f"QPushButton:disabled{{background-color:#888;}}")

        # ---------------- Helpers ----------------
        def pick_src(self):
            d = QFileDialog.getExistingDirectory(self, "Escolha a pasta FONTE (A)")
            if d:
                self.ed_src.setText(d)

        def pick_dst(self):
            d = QFileDialog.getExistingDirectory(self, "Escolha a pasta DESTINO (B)")
            if d:
                self.ed_dst.setText(d)

        def get_checked_flags(self):
            return [op["flag"] for op, cb in zip(self.options, self.checks) if cb.isChecked()]

        def delta_flags(self):
            # --no-whole-file força o algoritmo delta do rsync mesmo em cópia local
            return ["--no-whole-file"] if self.chk_delta.isChecked() else []

        def cor_atual(self):
            i = self.cmb_cor.currentIndex()
            return CORES[i][1], CORES[i][2]

        def _update_preview(self):
            flags = self.get_checked_flags() + self.delta_flags()
            cmd = build_command(flags, self.ed_src.text(),
                                self.ed_dst.text(), self.ed_xf.text(), self.ed_xd.text())
            self.preview.setPlainText(preview_string(cmd))

        def _check_rsync(self):
            if not shutil.which("rsync"):
                self.banner.setText("  rsync não encontrado. Instale com:  " + install_hint())
                self.banner.setVisible(True)

        # ---------------- Execução ----------------
        def _executar(self, flags, dry_run=False):
            src = format_path(self.ed_src.text())
            dst = format_path(self.ed_dst.text())
            if not src or not dst:
                QMessageBox.warning(self, "CSSync", "Informe a pasta FONTE e a pasta DESTINO.")
                return
            if not os.path.isdir(src):
                QMessageBox.warning(self, "CSSync", f"A pasta FONTE não existe:\n{src}")
                return
            if os.path.abspath(src) == os.path.abspath(dst):
                QMessageBox.warning(self, "CSSync", "A FONTE e o DESTINO são a mesma pasta.")
                return
            if not shutil.which("rsync"):
                QMessageBox.critical(self, "CSSync",
                                     "rsync não encontrado.\n\nInstale com:\n" + install_hint())
                return

            flags = list(flags) + self.delta_flags()
            cmd = build_command(flags, self.ed_src.text(), self.ed_dst.text(),
                                self.ed_xf.text(), self.ed_xd.text())
            self.preview.setPlainText(preview_string(cmd))

            if (not dry_run) and ("--delete" in flags):
                r = QMessageBox.question(
                    self, "Confirmar espelhamento",
                    "ATENÇÃO — modo ESPELHAR:\n\n"
                    "Tudo que existir no DESTINO (B) e não existir na FONTE (A) será APAGADO.\n\n"
                    "Dica: rode 'Simular' antes para conferir.\n\nDeseja continuar?")
                if r != QMessageBox.Yes:
                    return

            bg, fg = self.cor_atual()
            dlg = ConsoleDialog(self, cmd, retries=1, wait=2, bg=bg, fg=fg, dry_run=dry_run)
            dlg.exec()

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
            dlg = QDialog(self)
            dlg.setWindowTitle("Ajuda — CSSync")
            dlg.resize(860, 680)
            lay = QVBoxLayout(dlg)
            view = QPlainTextEdit()  # usaremos HTML via QTextEdit
            from PySide6.QtWidgets import QTextEdit
            view = QTextEdit()
            view.setReadOnly(True)
            view.setHtml(self._help_html())
            lay.addWidget(view, 1)
            b = QPushButton("Fechar")
            b.clicked.connect(dlg.accept)
            hb = QHBoxLayout(); hb.addStretch(1); hb.addWidget(b); hb.addStretch(1)
            lay.addLayout(hb)
            dlg.exec()

        def _help_html(self):
            cinza = "#777777"; preto = "#282828"; perigo = COR_PERIGO
            return f"""
            <div style="font-family:sans-serif;font-size:14px;color:{preto};">
            <h2>Os 3 modos de cópia</h2>

            <p><b style="color:{COR_ATUALIZAR};font-size:15px;">ATUALIZAR BACKUP (A → B)</b>
            <span style="color:{cinza};">— o botão do dia a dia</span><br>
            Copia arquivos <b>novos e alterados</b> de A para B (compara data e tamanho) e pula os idênticos.
            <b>Não apaga nada</b> em B: mesmo que você apague algo em A por engano, o backup continua em B.</p>

            <p><b style="color:{COR_ESPELHAR};font-size:15px;">ESPELHAR (A → B)</b>
            <span style="color:{cinza};">— use com atenção</span><br>
            B fica <b>idêntico</b> a A: copia novos e alterados E TAMBÉM
            <b style="color:{perigo};">apaga de B tudo que não existe mais em A.</b>
            Sempre pede confirmação antes de executar.</p>

            <p><b style="color:{COR_NOVOS};font-size:15px;">SÓ ARQUIVOS NOVOS EM B</b>
            <span style="color:{cinza};">— não toca no que já existe</span><br>
            Copia apenas o que <b>não existe</b> em B. Não atualiza arquivos alterados e não apaga nada.</p>

            <p><b style="color:{COR_SIMULAR};font-size:15px;">SIMULAR — 100% seguro</b><br>
            Apenas <b>lista</b> o que seria copiado ou apagado, sem fazer nada de verdade.
            Recomendado: simule antes do primeiro espelhamento.</p>

            <h3>⚡ Cópia delta — diferencial do Linux</h3>
            <p>Marque <b>Cópia delta</b> para o rsync enviar <b>apenas as partes que mudaram</b> de cada
            arquivo, em vez de recopiar o arquivo inteiro. Faz enorme diferença em arquivos grandes que
            mudam pouco — bancos de dados, máquinas virtuais, vídeos, arquivos PST. Aplica-se a <b>todos
            os modos</b> (Atualizar, Espelhar, Só novos, Executar marcadas e Simular). Tecnicamente, força
            o algoritmo delta (<code>--no-whole-file</code>) mesmo em cópia local — algo que o robocopy do
            Windows não faz.</p>

            <h3>Código de saída (no fim da cópia)</h3>
            <p>0 = tudo certo. &nbsp; <b style="color:{perigo};">diferente de 0 = algum arquivo não pôde ser copiado</b>
            (veja as mensagens na janela da cópia).</p>

            <h3>Dicas</h3>
            <ul>
            <li>Pendrive ou HD em FAT32/exFAT: marque <i>Tolerância de 1s na data</i> para evitar recópias.</li>
            <li>Arquivos negando acesso (donos/permissões): abra o app com <b>sudo</b> e marque dono, grupo e ACLs.</li>
            <li>Registro do que foi copiado: marque <b>--log-file</b> (gera cssync.log na sua pasta).</li>
            <li>A cor escolhida em <i>Cor do texto da cópia</i> vale para a janela do console da cópia.</li>
            </ul>

            <p style="color:{cinza};font-size:12px;">CSSync v{APP_VERSION} (Linux/Qt · rsync) — © 2026 Cristiano Silveira Silva — CC BY 4.0</p>
            </div>
            """


def main():
    if not QT_AVAILABLE:
        print("PySide6 (Qt) não está instalado.\nInstale com:\n  " + install_hint())
        sys.exit(1)
    if not shutil.which("rsync"):
        print("Aviso: rsync não encontrado. O app abre, mas instale com:\n  " + install_hint())
    app = QApplication(sys.argv)
    app.setApplicationName("CSSync")
    win = CSSyncWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

#!/usr/bin/env bash
# Gera os pacotes .deb do Robocopy Fácil (versão Qt e versão Tkinter).
# Requisito: dpkg-deb (já vem nas distros Debian/Ubuntu).
# Uso:  bash packaging/build-deb.sh
set -e

VER="1.2.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
DIST="$ROOT/dist"
WORK="$(mktemp -d)"
mkdir -p "$DIST"

build_one () {
  # $1=nome  $2=fonte_py  $3=depends  $4=descricao  $5=arquivo_saida
  local variant="$1" src="$2" deps="$3" descline="$4" outfile="$5"
  local D="$WORK/$variant"
  mkdir -p "$D/DEBIAN" "$D/usr/bin" "$D/usr/lib/robocopy-facil" \
           "$D/usr/share/applications" "$D/usr/share/icons/hicolor/scalable/apps" \
           "$D/usr/share/doc/robocopy-facil"

  install -m 0755 "$SCRIPT_DIR/robocopy-facil"         "$D/usr/bin/robocopy-facil"
  install -m 0644 "$ROOT/$src"                         "$D/usr/lib/robocopy-facil/robocopy_facil_linux.py"
  install -m 0644 "$SCRIPT_DIR/robocopy-facil.desktop" "$D/usr/share/applications/robocopy-facil.desktop"
  install -m 0644 "$SCRIPT_DIR/robocopy-facil.svg"     "$D/usr/share/icons/hicolor/scalable/apps/robocopy-facil.svg"

  cat > "$D/DEBIAN/control" <<EOF
Package: robocopy-facil
Version: ${VER}
Section: utils
Priority: optional
Architecture: all
Depends: ${deps}
Maintainer: Cristiano Silveira Silva <noreply@localhost>
Description: ${descline}
 Porte para Linux do Robocopy Facil (Windows). Tres modos de um clique
 (Atualizar, Espelhar, So novos), simulacao segura, pre-visualizacao do
 comando e exclusoes. Usa o rsync por baixo.
EOF

  cat > "$D/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database -q /usr/share/applications || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
exit 0
EOF
  chmod 0755 "$D/DEBIAN/postinst"

  cat > "$D/usr/share/doc/robocopy-facil/copyright" <<EOF
Robocopy Facil (porte Linux) - Autor: Cristiano Silveira Silva
Licenca: Creative Commons Atribuicao 4.0 (CC BY 4.0)
https://creativecommons.org/licenses/by/4.0/deed.pt-br
EOF

  dpkg-deb --build --root-owner-group "$D" "$DIST/$outfile" >/dev/null
  echo "  gerado: dist/$outfile"
}

echo "Gerando .deb (Qt — Debian 13+ / Ubuntu 24.10+)..."
build_one qt robocopy_facil_qt.py \
  "python3-pyside6.qtwidgets, python3-pyside6.qtgui, python3-pyside6.qtcore, rsync" \
  "Interface grafica nativa Qt para o rsync (porte do Robocopy Facil)" \
  "robocopy-facil_${VER}_all.deb"

echo "Gerando .deb (Tkinter — Debian 12)..."
build_one tk robocopy_facil_tk.py \
  "python3, python3-tk, rsync" \
  "Interface grafica (Tkinter) para o rsync - porte do Robocopy Facil" \
  "robocopy-facil_${VER}_tkinter_all.deb"

rm -rf "$WORK"
echo "Concluido."

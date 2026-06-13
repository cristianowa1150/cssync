#!/usr/bin/env bash
# Gera o pacote .rpm (versão Qt) do Robocopy Fácil.
# Requisito: rpmbuild  (pacote 'rpm-build' no Fedora; pacote 'rpm' no Debian/Ubuntu).
# Uso:  bash packaging/build-rpm.sh
set -e

VER="1.2.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
DIST="$ROOT/dist"
mkdir -p "$DIST"

TOP="$(mktemp -d)"
mkdir -p "$TOP/BUILD" "$TOP/BUILDROOT" "$TOP/RPMS" "$TOP/SOURCES" "$TOP/SPECS" "$TOP/SRPMS"

# Reúne os arquivos num local fixo que o spec referencia
STAGE="$TOP/stage"
mkdir -p "$STAGE"
cp "$ROOT/robocopy_facil_qt.py"        "$STAGE/robocopy_facil_linux.py"
cp "$SCRIPT_DIR/robocopy-facil"        "$STAGE/robocopy-facil"
cp "$SCRIPT_DIR/robocopy-facil.desktop" "$STAGE/robocopy-facil.desktop"
cp "$SCRIPT_DIR/robocopy-facil.svg"    "$STAGE/robocopy-facil.svg"

cat > "$TOP/SPECS/robocopy-facil.spec" <<SPEC
%global debug_package %{nil}
%global __brp_python_bytecompile %{nil}

Name:           robocopy-facil
Version:        ${VER}
Release:        1
Summary:        Interface grafica nativa Qt para o rsync (porte do Robocopy Facil)
License:        CC-BY-4.0
URL:            https://github.com/cristianowa1150/robocopy-facil
BuildArch:      noarch
AutoReqProv:    no
Requires:       python3
Requires:       python3-pyside6
Requires:       rsync

%description
Porte para Linux do Robocopy Facil (Windows), com interface nativa Qt/Plasma.
Tres modos de um clique (Atualizar, Espelhar, So novos), simulacao segura,
pre-visualizacao do comando e exclusoes. Usa o rsync por baixo.

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}/usr/bin %{buildroot}/usr/lib/robocopy-facil %{buildroot}/usr/share/applications %{buildroot}/usr/share/icons/hicolor/scalable/apps
install -m 0755 ${STAGE}/robocopy-facil %{buildroot}/usr/bin/robocopy-facil
install -m 0644 ${STAGE}/robocopy_facil_linux.py %{buildroot}/usr/lib/robocopy-facil/robocopy_facil_linux.py
install -m 0644 ${STAGE}/robocopy-facil.desktop %{buildroot}/usr/share/applications/robocopy-facil.desktop
install -m 0644 ${STAGE}/robocopy-facil.svg %{buildroot}/usr/share/icons/hicolor/scalable/apps/robocopy-facil.svg

%post
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database -q /usr/share/applications || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
exit 0

%files
/usr/bin/robocopy-facil
%dir /usr/lib/robocopy-facil
/usr/lib/robocopy-facil/robocopy_facil_linux.py
/usr/share/applications/robocopy-facil.desktop
/usr/share/icons/hicolor/scalable/apps/robocopy-facil.svg

%changelog
* Fri Jun 12 2026 Cristiano Silveira Silva <noreply@localhost> - ${VER}-1
- Versao nativa Qt (PySide6) para KDE/Plasma
SPEC

rpmbuild -bb --define "_topdir $TOP" "$TOP/SPECS/robocopy-facil.spec"
RPM="$(find "$TOP/RPMS" -name '*.rpm' | head -1)"
cp "$RPM" "$DIST/"
echo "  gerado: dist/$(basename "$RPM")"
rm -rf "$TOP"
echo "Concluido."

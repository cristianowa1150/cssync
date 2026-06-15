#!/usr/bin/env bash
# Gera o pacote .rpm (versão Qt) do CSSync.
# Requisito: rpmbuild  (pacote 'rpm-build' no Fedora; pacote 'rpm' no Debian/Ubuntu).
# Uso:  bash packaging/build-rpm.sh
set -e

VER="1.6.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
DIST="$ROOT/dist"
mkdir -p "$DIST"

TOP="$(mktemp -d)"
mkdir -p "$TOP/BUILD" "$TOP/BUILDROOT" "$TOP/RPMS" "$TOP/SOURCES" "$TOP/SPECS" "$TOP/SRPMS"

# Reúne os arquivos num local fixo que o spec referencia
STAGE="$TOP/stage"
mkdir -p "$STAGE"
cp "$ROOT/cssync_qt.py"        "$STAGE/cssync_linux.py"
cp "$SCRIPT_DIR/cssync"        "$STAGE/cssync"
cp "$SCRIPT_DIR/cssync.desktop" "$STAGE/cssync.desktop"
cp "$SCRIPT_DIR/cssync.svg"    "$STAGE/cssync.svg"

cat > "$TOP/SPECS/cssync.spec" <<SPEC
%global debug_package %{nil}
%global __brp_python_bytecompile %{nil}

Name:           cssync
Version:        ${VER}
Release:        1
Summary:        Interface grafica nativa Qt para o rsync (porte do CSSync)
License:        CC-BY-4.0
URL:            https://github.com/cristianowa1150/cssync
BuildArch:      noarch
AutoReqProv:    no
Requires:       python3
Requires:       python3-pyside6
Requires:       rsync

%description
Porte para Linux do CSSync (Windows), com interface nativa Qt/Plasma.
Tres modos de um clique (Atualizar, Espelhar, So novos), simulacao segura,
pre-visualizacao do comando e exclusoes. Usa o rsync por baixo.

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}/usr/bin %{buildroot}/usr/lib/cssync %{buildroot}/usr/share/applications %{buildroot}/usr/share/icons/hicolor/scalable/apps
install -m 0755 ${STAGE}/cssync %{buildroot}/usr/bin/cssync
install -m 0644 ${STAGE}/cssync_linux.py %{buildroot}/usr/lib/cssync/cssync_linux.py
install -m 0644 ${STAGE}/cssync.desktop %{buildroot}/usr/share/applications/cssync.desktop
install -m 0644 ${STAGE}/cssync.svg %{buildroot}/usr/share/icons/hicolor/scalable/apps/cssync.svg

%post
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database -q /usr/share/applications || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
exit 0

%files
/usr/bin/cssync
%dir /usr/lib/cssync
/usr/lib/cssync/cssync_linux.py
/usr/share/applications/cssync.desktop
/usr/share/icons/hicolor/scalable/apps/cssync.svg

%changelog
* Mon Jun 15 2026 Cristiano Silveira Silva <noreply@localhost> - ${VER}-1
- Opcao de copia delta (rsync --no-whole-file) em todos os modos
- Fonte maior na lista de opcoes
* Fri Jun 12 2026 Cristiano Silveira Silva <noreply@localhost> - 1.5.0-1
- Versao nativa Qt (PySide6) para KDE/Plasma
SPEC

rpmbuild -bb --define "_topdir $TOP" "$TOP/SPECS/cssync.spec"
RPM="$(find "$TOP/RPMS" -name '*.rpm' | head -1)"
cp "$RPM" "$DIST/"
echo "  gerado: dist/$(basename "$RPM")"
rm -rf "$TOP"
echo "Concluido."

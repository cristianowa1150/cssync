# =====================================================================
#  Gera o executavel CSSync.exe a partir do CSSync.ps1
#  Requer o modulo ps2exe:  Install-Module ps2exe -Scope CurrentUser
#  © 2026 Cristiano Silveira Silva
# =====================================================================

$versao = '1.6.0.0'

if (-not (Get-Module -ListAvailable ps2exe)) {
    Write-Host 'Instalando o modulo ps2exe...'
    Install-Module ps2exe -Scope CurrentUser -Force
}

Invoke-ps2exe `
    -inputFile  (Join-Path $PSScriptRoot 'CSSync.ps1') `
    -outputFile (Join-Path $PSScriptRoot 'CSSync.exe') `
    -iconFile   (Join-Path $PSScriptRoot 'cssync.ico') `
    -noConsole -STA `
    -title       'CSSync' `
    -description 'Interface gráfica fácil para o Robocopy do Windows' `
    -company     'Cristiano Silveira Silva' `
    -copyright   '© 2026 Cristiano Silveira Silva' `
    -product     'CSSync' `
    -version     $versao

$exe = Get-Item (Join-Path $PSScriptRoot 'CSSync.exe')
"Gerado: {0} v{1} ({2:N0} KB)" -f $exe.Name, $versao, ($exe.Length / 1KB)

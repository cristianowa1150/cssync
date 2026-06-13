# =====================================================================
#  Gera o executavel RobocopyFacil.exe a partir do RobocopyFacil.ps1
#  Requer o modulo ps2exe:  Install-Module ps2exe -Scope CurrentUser
#  © 2026 Cristiano Silveira Silva
# =====================================================================

$versao = '1.3.0.0'

if (-not (Get-Module -ListAvailable ps2exe)) {
    Write-Host 'Instalando o modulo ps2exe...'
    Install-Module ps2exe -Scope CurrentUser -Force
}

Invoke-ps2exe `
    -inputFile  (Join-Path $PSScriptRoot 'RobocopyFacil.ps1') `
    -outputFile (Join-Path $PSScriptRoot 'RobocopyFacil.exe') `
    -iconFile   (Join-Path $PSScriptRoot 'robocopy-facil.ico') `
    -noConsole -STA `
    -title       'Robocopy Fácil' `
    -description 'Interface gráfica fácil para o Robocopy do Windows' `
    -company     'Cristiano Silveira Silva' `
    -copyright   '© 2026 Cristiano Silveira Silva' `
    -product     'Robocopy Fácil' `
    -version     $versao

$exe = Get-Item (Join-Path $PSScriptRoot 'RobocopyFacil.exe')
"Gerado: {0} v{1} ({2:N0} KB)" -f $exe.Name, $versao, ($exe.Length / 1KB)

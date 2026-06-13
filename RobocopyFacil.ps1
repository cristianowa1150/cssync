# =====================================================================
#  Robocopy Facil v1.3 — interface grafica simples para o Robocopy do Windows
#  © 2026 Cristiano Silveira Silva — Licença CC BY 4.0
#  Requisitos: nenhum. Usa apenas PowerShell + .NET, ja incluidos no Windows.
#  Para abrir: clique duas vezes em "Iniciar - Robocopy Facil.bat"
# =====================================================================

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()

# ---------------------------------------------------------------------
# Opções do robocopy mostradas na tela (flag, marcado por padrão, explicação)
# ---------------------------------------------------------------------
$opcoes = @(
    @{ Flag = '/E';         Marcado = $true;  Desc = 'Copia todas as subpastas, inclusive as vazias' }
    @{ Flag = '/Z';         Marcado = $false; Desc = 'Modo reiniciável: retoma a cópia do ponto onde parou se for interrompida' }
    @{ Flag = '/MT:8';      Marcado = $true;  Desc = 'Copia 8 arquivos em paralelo (muito mais rápido com muitos arquivos)' }
    @{ Flag = '/R:1';       Marcado = $true;  Desc = 'Em caso de erro, tenta de novo só 1 vez (o padrão do robocopy é 1 milhão!)' }
    @{ Flag = '/W:2';       Marcado = $true;  Desc = 'Espera 2 segundos entre as tentativas' }
    @{ Flag = '/DCOPY:DAT'; Marcado = $true;  Desc = 'Mantém também a data e os atributos das PASTAS copiadas' }
    @{ Flag = '/XO';        Marcado = $false; Desc = 'Protege o destino: se o arquivo em B for mais novo que em A, ele é mantido' }
    @{ Flag = '/FFT';       Marcado = $false; Desc = 'Tolerância de 2s na data do arquivo (use com pendrive, rede ou FAT32)' }
    @{ Flag = '/XJ';        Marcado = $true;  Desc = 'Ignora junções/links simbólicos (evita loops infinitos)' }
    @{ Flag = '/XA:SH';     Marcado = $false; Desc = 'Não copia arquivos ocultos nem de sistema' }
    @{ Flag = '/SL';        Marcado = $false; Desc = 'Copia atalhos simbólicos como atalhos (sem copiar o conteúdo apontado)' }
    @{ Flag = '/B';         Marcado = $false; Desc = 'Modo backup: lê arquivos mesmo sem permissão (abrir como administrador)' }
    @{ Flag = '/COPYALL';   Marcado = $false; Desc = 'Copia tudo: dados, datas, atributos e permissões NTFS (administrador)' }
    @{ Flag = '/J';         Marcado = $false; Desc = 'Cópia sem buffer: melhor para arquivos muito grandes (vídeos, ISOs)' }
    @{ Flag = '/ETA';       Marcado = $false; Desc = 'Mostra o tempo estimado para terminar cada arquivo' }
    @{ Flag = '/NP';        Marcado = $false; Desc = 'Oculta o percentual de progresso (deixa a saída mais limpa)' }
    @{ Flag = '/V';         Marcado = $false; Desc = 'Modo detalhado: mostra também os arquivos que foram ignorados' }
    @{ Flag = ('/TEE /LOG+:"{0}\robocopy-facil.log"' -f $env:USERPROFILE); Marcado = $false; Desc = 'Salva um registro da cópia em robocopy-facil.log na sua pasta de usuário' }
    @{ Flag = '/MIR';       Marcado = $false; Desc = 'ESPELHAR: destino fica IDÊNTICO à origem (APAGA de B o que não existe em A!)' }
)

# Flags de desempenho/segurança usadas pelos três botões de modo
$flagsBase = @('/MT:8', '/R:1', '/W:2', '/XJ', '/DCOPY:DAT')

# Pastas e arquivos de sistema do Windows que nunca devem ir para backup.
# Evita erros de acesso negado ao copiar a raiz de um drive e, no modo
# espelhar, também protege essas pastas do DESTINO contra exclusão.
$exclusoesSistema = @(
    '/XD', '"$RECYCLE.BIN"', '"System Volume Information"', '"Recovery"',
    '/XF', '"pagefile.sys"', '"hiberfil.sys"', '"swapfile.sys"'
)

# Cores dos modos (usadas nos botões e na Ajuda)
$corAtualizar = [System.Drawing.Color]::FromArgb(34, 120, 70)
$corEspelhar  = [System.Drawing.Color]::FromArgb(192, 84, 22)
$corNovos     = [System.Drawing.Color]::FromArgb(30, 90, 160)
$corSimular   = [System.Drawing.Color]::FromArgb(100, 60, 150)
$corPerigo    = [System.Drawing.Color]::Firebrick

# ---------------------------------------------------------------------
# Janela principal
# ---------------------------------------------------------------------
$form                 = New-Object System.Windows.Forms.Form
$form.Text            = 'Robocopy Fácil  —  copiar FONTE (A)  →  DESTINO (B)'
$form.ClientSize      = New-Object System.Drawing.Size(940, 798)
$form.StartPosition   = 'CenterScreen'
$form.FormBorderStyle = 'FixedSingle'
$form.MaximizeBox     = $false
$form.Font            = New-Object System.Drawing.Font('Segoe UI', 12)

# Ícone da janela: do próprio .exe (quando compilado) ou do .ico ao lado do script
try {
    $exeAtual = [System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName
    if ($exeAtual -notmatch 'powershell|pwsh') {
        $form.Icon = [System.Drawing.Icon]::ExtractAssociatedIcon($exeAtual)
    } elseif (Test-Path (Join-Path $PSScriptRoot 'robocopy-facil.ico')) {
        $form.Icon = New-Object System.Drawing.Icon((Join-Path $PSScriptRoot 'robocopy-facil.ico'))
    }
} catch {}

$tooltip = New-Object System.Windows.Forms.ToolTip
$tooltip.AutoPopDelay = 20000

$fontNegrito = New-Object System.Drawing.Font('Segoe UI', 12, [System.Drawing.FontStyle]::Bold)

# ----- Pasta FONTE -----
$lblSrc          = New-Object System.Windows.Forms.Label
$lblSrc.Text     = 'Pasta FONTE (A) — de onde os arquivos vêm:'
$lblSrc.Location = New-Object System.Drawing.Point(12, 10)
$lblSrc.AutoSize = $true
$lblSrc.Font     = $fontNegrito

$txtSrc          = New-Object System.Windows.Forms.TextBox
$txtSrc.Location = New-Object System.Drawing.Point(12, 38)
$txtSrc.Size     = New-Object System.Drawing.Size(760, 30)

$btnSrc          = New-Object System.Windows.Forms.Button
$btnSrc.Text     = 'Procurar...'
$btnSrc.Location = New-Object System.Drawing.Point(780, 36)
$btnSrc.Size     = New-Object System.Drawing.Size(148, 34)

# ----- Pasta DESTINO -----
$lblDst          = New-Object System.Windows.Forms.Label
$lblDst.Text     = 'Pasta DESTINO (B) — para onde os arquivos vão (criada se não existir):'
$lblDst.Location = New-Object System.Drawing.Point(12, 80)
$lblDst.AutoSize = $true
$lblDst.Font     = $fontNegrito

$txtDst          = New-Object System.Windows.Forms.TextBox
$txtDst.Location = New-Object System.Drawing.Point(12, 108)
$txtDst.Size     = New-Object System.Drawing.Size(760, 30)

$btnDst          = New-Object System.Windows.Forms.Button
$btnDst.Text     = 'Procurar...'
$btnDst.Location = New-Object System.Drawing.Point(780, 106)
$btnDst.Size     = New-Object System.Drawing.Size(148, 34)

# ----- Grupo de opções (com rolagem) -----
$grp          = New-Object System.Windows.Forms.GroupBox
$grp.Text     = ' Opções do robocopy — role a lista para ver todas '
$grp.Location = New-Object System.Drawing.Point(12, 150)
$grp.Size     = New-Object System.Drawing.Size(916, 292)

$painel            = New-Object System.Windows.Forms.Panel
$painel.Location   = New-Object System.Drawing.Point(8, 30)
$painel.Size       = New-Object System.Drawing.Size(900, 252)
$painel.AutoScroll = $true
$grp.Controls.Add($painel)

$script:checkboxes = @()
$y = 4
foreach ($op in $opcoes) {
    $cb          = New-Object System.Windows.Forms.CheckBox
    $cb.Text     = ('{0}   —   {1}' -f ($op.Flag -split ' ')[0], $op.Desc)
    $cb.Tag      = $op.Flag
    $cb.Checked  = $op.Marcado
    $cb.Location = New-Object System.Drawing.Point(4, $y)
    $cb.Size     = New-Object System.Drawing.Size(860, 30)
    if ($op.Flag -eq '/MIR') {
        $cb.ForeColor = $corPerigo
        $tooltip.SetToolTip($cb, "CUIDADO: /MIR torna o destino uma cópia exata da origem.`nArquivos que existem só no destino serão APAGADOS.")
    }
    $painel.Controls.Add($cb)
    $script:checkboxes += $cb
    $y += 32
}

# ----- Exclusões -----
$lblXF          = New-Object System.Windows.Forms.Label
$lblXF.Text     = 'Excluir arquivos (/XF):'
$lblXF.Location = New-Object System.Drawing.Point(12, 453)
$lblXF.AutoSize = $true

$txtXF          = New-Object System.Windows.Forms.TextBox
$txtXF.Location = New-Object System.Drawing.Point(210, 450)
$txtXF.Size     = New-Object System.Drawing.Size(250, 30)

$lblXD          = New-Object System.Windows.Forms.Label
$lblXD.Text     = 'Excluir pastas (/XD):'
$lblXD.Location = New-Object System.Drawing.Point(485, 453)
$lblXD.AutoSize = $true

$txtXD          = New-Object System.Windows.Forms.TextBox
$txtXD.Location = New-Object System.Drawing.Point(663, 450)
$txtXD.Size     = New-Object System.Drawing.Size(265, 30)

$lblHint           = New-Object System.Windows.Forms.Label
$lblHint.Text      = 'Separe por ponto e vírgula. Ex.: *.tmp; *.bak   |   Ex. de pastas: node_modules; $RECYCLE.BIN'
$lblHint.Location  = New-Object System.Drawing.Point(12, 488)
$lblHint.Size      = New-Object System.Drawing.Size(916, 24)
$lblHint.Font      = New-Object System.Drawing.Font('Segoe UI', 10.5)
$lblHint.ForeColor = [System.Drawing.Color]::DimGray

# ----- Cor do texto da janela de cópia -----
# Códigos do comando "color" do cmd: fundo preto + cor da fonte
$mapaCores = [ordered]@{
    'Verde (estilo Linux)'    = '0A'
    'Padrão (cinza claro)'    = ''
    'Branco brilhante'        = '0F'
    'Amarelo'                 = '0E'
    'Ciano'                   = '0B'
    'Vermelho claro'          = '0C'
    'Magenta'                 = '0D'
    'Preto sobre branco'      = 'F0'
}

$lblCor          = New-Object System.Windows.Forms.Label
$lblCor.Text     = 'Cor do texto da cópia:'
$lblCor.Location = New-Object System.Drawing.Point(490, 516)
$lblCor.AutoSize = $true

$cmbCor               = New-Object System.Windows.Forms.ComboBox
$cmbCor.DropDownStyle = 'DropDownList'
$cmbCor.Location      = New-Object System.Drawing.Point(688, 511)
$cmbCor.Size          = New-Object System.Drawing.Size(240, 30)
$cmbCor.Items.AddRange([string[]]@($mapaCores.Keys))
$cmbCor.SelectedIndex = 0
$tooltip.SetToolTip($cmbCor, 'Cor da fonte da janela de console onde a cópia roda (comando "color" do cmd).')

# ----- Pré-visualização do comando -----
$lblPrev          = New-Object System.Windows.Forms.Label
$lblPrev.Text     = 'Comando que será executado:'
$lblPrev.Location = New-Object System.Drawing.Point(12, 516)
$lblPrev.AutoSize = $true
$lblPrev.Font     = $fontNegrito

$txtPrev           = New-Object System.Windows.Forms.TextBox
$txtPrev.Location  = New-Object System.Drawing.Point(12, 544)
$txtPrev.Size      = New-Object System.Drawing.Size(916, 58)
$txtPrev.Multiline = $true
$txtPrev.ReadOnly  = $true
$txtPrev.BackColor = [System.Drawing.Color]::WhiteSmoke
$txtPrev.Font      = New-Object System.Drawing.Font('Consolas', 11)

# ----- Botão principal: atualizar backup (novos + alterados) -----
$btnAtualizar           = New-Object System.Windows.Forms.Button
$btnAtualizar.Text      = '▶  ATUALIZAR BACKUP (A → B) — copia NOVOS e ALTERADOS, não apaga nada em B'
$btnAtualizar.Location  = New-Object System.Drawing.Point(12, 610)
$btnAtualizar.Size      = New-Object System.Drawing.Size(916, 50)
$btnAtualizar.BackColor = $corAtualizar
$btnAtualizar.ForeColor = [System.Drawing.Color]::White
$btnAtualizar.FlatStyle = 'Flat'
$btnAtualizar.Font      = New-Object System.Drawing.Font('Segoe UI', 12.5, [System.Drawing.FontStyle]::Bold)
$tooltip.SetToolTip($btnAtualizar, "Comportamento padrão do robocopy com /E:`ncompara data e tamanho de cada arquivo, copia o que é novo ou foi alterado em A`ne pula o que está idêntico. Nada é apagado no destino.`nPastas de sistema (`$RECYCLE.BIN, System Volume Information) são ignoradas automaticamente.")

# ----- Botão espelhar -----
$btnEspelhar           = New-Object System.Windows.Forms.Button
$btnEspelhar.Text      = '⟳  ESPELHAR (A → B) — B fica IDÊNTICO a A (apaga de B o que não existe em A)'
$btnEspelhar.Location  = New-Object System.Drawing.Point(12, 666)
$btnEspelhar.Size      = New-Object System.Drawing.Size(916, 46)
$btnEspelhar.BackColor = $corEspelhar
$btnEspelhar.ForeColor = [System.Drawing.Color]::White
$btnEspelhar.FlatStyle = 'Flat'
$btnEspelhar.Font      = New-Object System.Drawing.Font('Segoe UI', 12, [System.Drawing.FontStyle]::Bold)
$tooltip.SetToolTip($btnEspelhar, "Usa /MIR: além de copiar novos e alterados, APAGA do destino`ntudo que não existir mais na origem. Pede confirmação antes.`nPastas de sistema (`$RECYCLE.BIN, System Volume Information) são ignoradas`nna cópia e protegidas contra exclusão no destino.")

# ----- Botões secundários -----
$btnExec           = New-Object System.Windows.Forms.Button
$btnExec.Text      = 'Executar opções marcadas'
$btnExec.Location  = New-Object System.Drawing.Point(12, 718)
$btnExec.Size      = New-Object System.Drawing.Size(266, 42)

$btnSim            = New-Object System.Windows.Forms.Button
$btnSim.Text       = 'Simular (/L) — não copia'
$btnSim.Location   = New-Object System.Drawing.Point(286, 718)
$btnSim.Size       = New-Object System.Drawing.Size(254, 42)
$btnSim.ForeColor  = $corSimular
$tooltip.SetToolTip($btnSim, "100% seguro: o /L apenas LISTA o que seria feito.`nNão copia, não altera e não apaga nada — nem em A, nem em B.")

$btnNovos           = New-Object System.Windows.Forms.Button
$btnNovos.Text      = 'Só arquivos NOVOS em B'
$btnNovos.Location  = New-Object System.Drawing.Point(548, 718)
$btnNovos.Size      = New-Object System.Drawing.Size(254, 42)
$btnNovos.ForeColor = $corNovos
$tooltip.SetToolTip($btnNovos, "Usa /E /XC /XN /XO: copia apenas o que NÃO existe no destino.`nArquivos alterados NÃO são atualizados — para isso use o botão verde ATUALIZAR.")

$btnAjuda           = New-Object System.Windows.Forms.Button
$btnAjuda.Text      = '?  Ajuda'
$btnAjuda.Location  = New-Object System.Drawing.Point(810, 718)
$btnAjuda.Size      = New-Object System.Drawing.Size(118, 42)
$btnAjuda.Font      = $fontNegrito
$btnAjuda.ForeColor = $corNovos

# ----- Rodapé -----
$lblRodape           = New-Object System.Windows.Forms.Label
$lblRodape.Text      = 'v1.3 — © 2026 Cristiano Silveira Silva   |   Códigos de saída 0 a 7 = sucesso (0 = nada a copiar, 1 = copiou); 8 ou mais = erro.'
$lblRodape.Location  = New-Object System.Drawing.Point(12, 768)
$lblRodape.Size      = New-Object System.Drawing.Size(916, 26)
$lblRodape.Font      = New-Object System.Drawing.Font('Segoe UI', 10.5)
$lblRodape.ForeColor = [System.Drawing.Color]::DimGray

$form.Controls.AddRange(@($lblSrc, $txtSrc, $btnSrc, $lblDst, $txtDst, $btnDst, $grp,
    $lblXF, $txtXF, $lblXD, $txtXD, $lblHint, $lblCor, $cmbCor, $lblPrev, $txtPrev,
    $btnAtualizar, $btnEspelhar, $btnExec, $btnSim, $btnNovos, $btnAjuda, $lblRodape))

# ---------------------------------------------------------------------
# Funções
# ---------------------------------------------------------------------
function Format-Caminho([string]$p) {
    $p = $p.Trim().Trim('"').TrimEnd('\')
    # Raiz de drive ("C:") precisa de tratamento para não quebrar as aspas no cmd
    if ($p -match '^[A-Za-z]:$') { $p += '\.' }
    return $p
}

function Get-FlagsMarcadas {
    $flags = @()
    foreach ($cb in $script:checkboxes) {
        if ($cb.Checked) { $flags += [string]$cb.Tag }
    }
    return $flags
}

function Get-ListaExtra([string]$texto, [string]$flag) {
    $itens = @($texto -split ';' | ForEach-Object { $_.Trim().Trim('"') } | Where-Object { $_ })
    if ($itens.Count -eq 0) { return '' }
    return ($flag + ' ' + (($itens | ForEach-Object { '"{0}"' -f $_ }) -join ' '))
}

function Build-Comando([string[]]$flags) {
    $src = Format-Caminho $txtSrc.Text
    $dst = Format-Caminho $txtDst.Text
    $cmd = 'robocopy "{0}" "{1}" {2}' -f $src, $dst, ($flags -join ' ')
    $xf = Get-ListaExtra $txtXF.Text '/XF'
    $xd = Get-ListaExtra $txtXD.Text '/XD'
    if ($xf) { $cmd += ' ' + $xf }
    if ($xd) { $cmd += ' ' + $xd }
    return $cmd
}

function Update-Preview {
    $txtPrev.Text = Build-Comando (Get-FlagsMarcadas)
}

function Executar([string[]]$flags) {
    $src = Format-Caminho $txtSrc.Text
    $dst = Format-Caminho $txtDst.Text

    if (-not $src -or -not $dst) {
        [void][System.Windows.Forms.MessageBox]::Show('Informe a pasta FONTE e a pasta DESTINO.', 'Robocopy Fácil', 'OK', 'Warning')
        return
    }
    if (-not (Test-Path -LiteralPath $src)) {
        [void][System.Windows.Forms.MessageBox]::Show("A pasta FONTE não existe:`n$src", 'Robocopy Fácil', 'OK', 'Warning')
        return
    }
    if ($src -ieq $dst) {
        [void][System.Windows.Forms.MessageBox]::Show('A FONTE e o DESTINO são a mesma pasta.', 'Robocopy Fácil', 'OK', 'Warning')
        return
    }
    if (($flags -contains '/MIR') -and ($flags -notcontains '/L')) {
        $r = [System.Windows.Forms.MessageBox]::Show(
            "ATENÇÃO — modo ESPELHAR (/MIR):`n`nTudo que existir no DESTINO e não existir na FONTE será APAGADO.`n`nDeseja continuar?",
            'Confirmar espelhamento', 'YesNo', 'Warning')
        if ($r -ne 'Yes') { return }
    }

    $cmd = Build-Comando $flags
    $txtPrev.Text = $cmd

    # Executa num arquivo .cmd temporário: evita qualquer problema de aspas
    # e mantém a janela aberta para ver o relatório final do robocopy.
    $tmp = Join-Path $env:TEMP 'robocopy-facil.cmd'
    $linhas = New-Object 'System.Collections.Generic.List[string]'
    $linhas.Add('@echo off')
    $codCor = [string]$mapaCores[[string]$cmbCor.SelectedItem]
    if ($codCor) { $linhas.Add("color $codCor") }
    $linhas.Add('echo =================================================')
    $linhas.Add("echo  $cmd")
    $linhas.Add('echo =================================================')
    $linhas.Add('echo.')
    $linhas.Add($cmd)
    $linhas.Add('echo.')
    $linhas.Add('echo ===== Concluido. Codigo de saida: %ERRORLEVEL%  (0 a 7 = sucesso) =====')
    $linhas.Add('pause')
    $linhas | Set-Content -LiteralPath $tmp -Encoding Oem
    Start-Process cmd.exe -ArgumentList '/c', $tmp
}

function Escolher-Pasta([System.Windows.Forms.TextBox]$caixa, [string]$titulo) {
    $dlg = New-Object System.Windows.Forms.FolderBrowserDialog
    $dlg.Description = $titulo
    $dlg.ShowNewFolderButton = $true
    if ($caixa.Text -and (Test-Path -LiteralPath $caixa.Text)) { $dlg.SelectedPath = $caixa.Text }
    if ($dlg.ShowDialog() -eq 'OK') { $caixa.Text = $dlg.SelectedPath }
}

# ---------------------------------------------------------------------
# Janela de Ajuda (texto colorido)
# ---------------------------------------------------------------------
function Add-Ajuda($rtb, [string]$texto, [System.Drawing.Color]$cor, [bool]$negrito, [single]$tamanho) {
    $rtb.SelectionStart = $rtb.TextLength
    $rtb.SelectionLength = 0
    $rtb.SelectionColor = $cor
    if ($negrito) { $estilo = [System.Drawing.FontStyle]::Bold } else { $estilo = [System.Drawing.FontStyle]::Regular }
    $rtb.SelectionFont = New-Object System.Drawing.Font('Segoe UI', $tamanho, $estilo)
    $rtb.AppendText($texto)
}

function Mostrar-Ajuda {
    $fAjuda                 = New-Object System.Windows.Forms.Form
    $fAjuda.Text            = 'Ajuda — Robocopy Fácil'
    $fAjuda.ClientSize      = New-Object System.Drawing.Size(840, 680)
    $fAjuda.StartPosition   = 'CenterParent'
    $fAjuda.MinimizeBox     = $false
    $fAjuda.MaximizeBox     = $false

    $rtb             = New-Object System.Windows.Forms.RichTextBox
    $rtb.Dock        = 'Fill'
    $rtb.ReadOnly    = $true
    $rtb.BackColor   = [System.Drawing.Color]::White
    $rtb.BorderStyle = 'None'
    $rtb.ScrollBars  = 'Vertical'
    $fAjuda.Controls.Add($rtb)

    $preto = [System.Drawing.Color]::FromArgb(40, 40, 40)
    $cinza = [System.Drawing.Color]::DimGray

    Add-Ajuda $rtb "  OS 3 MODOS DE CÓPIA`n`n" $preto $true 15

    Add-Ajuda $rtb "  ATUALIZAR BACKUP (A → B)   " $corAtualizar $true 13
    Add-Ajuda $rtb "— o botão do dia a dia`n" $cinza $false 12
    Add-Ajuda $rtb "  Copia arquivos NOVOS e ALTERADOS de A para B (compara data e tamanho) e pula os idênticos.`n  NÃO apaga nada em B: mesmo que você delete algo em A por engano, o backup continua em B.`n`n" $preto $false 12

    Add-Ajuda $rtb "  ESPELHAR (A → B)   " $corEspelhar $true 13
    Add-Ajuda $rtb "— /MIR, use com atenção`n" $cinza $false 12
    Add-Ajuda $rtb "  B fica IDÊNTICO a A: copia novos e alterados E TAMBÉM " $preto $false 12
    Add-Ajuda $rtb "APAGA de B tudo que não existe mais em A. " $corPerigo $true 12
    Add-Ajuda $rtb "`n  Sempre pede confirmação antes de executar.`n`n" $preto $false 12

    Add-Ajuda $rtb "  SÓ ARQUIVOS NOVOS EM B   " $corNovos $true 13
    Add-Ajuda $rtb "— /XC /XN /XO`n" $cinza $false 12
    Add-Ajuda $rtb "  Copia apenas o que NÃO existe em B. Não atualiza arquivos alterados e não apaga nada.`n  Útil quando você quer ter certeza absoluta de que nada existente em B será tocado.`n`n" $preto $false 12

    Add-Ajuda $rtb "  SIMULAR (/L) — 100% seguro`n" $corSimular $true 13
    Add-Ajuda $rtb "  Apenas LISTA o que seria copiado ou apagado, sem fazer nada de verdade.`n  Não copia, não altera e não apaga nenhum arquivo — nem em A, nem em B.`n  A pasta FONTE (A) nunca é modificada pelo robocopy, em nenhum modo.`n  Recomendado: simule antes do primeiro espelhamento para conferir o que será feito.`n`n" $preto $false 12

    Add-Ajuda $rtb "  CÓDIGOS DE SAÍDA (mostrados no fim da cópia)`n" $preto $true 13
    Add-Ajuda $rtb "  0 = nada a copiar (tudo já estava em dia)`n  1 = arquivos copiados com sucesso`n  2 = há arquivos extras no destino (informativo)`n  4 = alguns arquivos/pastas incompatíveis foram ignorados`n  0 a 7 = sucesso  |  " $preto $false 12
    Add-Ajuda $rtb "8 ou mais = houve erro em algum arquivo`n`n" $corPerigo $true 12

    Add-Ajuda $rtb "  DICAS`n" $preto $true 13
    Add-Ajuda $rtb "  • Pendrive ou HD externo em FAT32/exFAT: marque /FFT para evitar recópias desnecessárias.`n  • Arquivos negando acesso: abra o aplicativo como administrador e marque /B.`n  • Quer um registro do que foi copiado: marque a opção /TEE (gera robocopy-facil.log).`n  • A cor escolhida em 'Cor do texto da cópia' vale para toda a janela de console da cópia.`n  • Os 3 botões de modo ignoram automaticamente pastas e arquivos de sistema do Windows:`n    `$RECYCLE.BIN, System Volume Information, Recovery, pagefile.sys, hiberfil.sys e swapfile.sys.`n`n" $preto $false 12

    Add-Ajuda $rtb "  Robocopy Fácil v1.3 — © 2026 Cristiano Silveira Silva — Licença CC BY 4.0`n" $cinza $false 11

    $rtb.SelectionStart = 0
    $rtb.ScrollToCaret()
    [void]$fAjuda.ShowDialog($form)
}

# ---------------------------------------------------------------------
# Eventos
# ---------------------------------------------------------------------
$btnSrc.Add_Click({ Escolher-Pasta $txtSrc 'Escolha a pasta FONTE (A)' })
$btnDst.Add_Click({ Escolher-Pasta $txtDst 'Escolha a pasta DESTINO (B)' })

$txtSrc.Add_TextChanged({ Update-Preview })
$txtDst.Add_TextChanged({ Update-Preview })
$txtXF.Add_TextChanged({ Update-Preview })
$txtXD.Add_TextChanged({ Update-Preview })
foreach ($cb in $script:checkboxes) { $cb.Add_CheckedChanged({ Update-Preview }) }

# ATUALIZAR: comportamento padrão do robocopy com /E — copia arquivos novos
# e alterados (compara data e tamanho), pula idênticos, não apaga nada em B.
$btnAtualizar.Add_Click({
    Executar (@('/E') + $flagsBase + $exclusoesSistema)
})

# ESPELHAR: /MIR = atualizar + apagar de B o que não existe em A (com confirmação).
$btnEspelhar.Add_Click({
    Executar (@('/MIR') + $flagsBase + $exclusoesSistema)
})

# SÓ NOVOS: /XC ignora alterados, /XN ignora mais novos, /XO ignora mais
# antigos -> copia apenas o que NÃO existe no destino.
$btnNovos.Add_Click({
    Executar (@('/E', '/XC', '/XN', '/XO') + $flagsBase + $exclusoesSistema)
})

$btnExec.Add_Click({ Executar (Get-FlagsMarcadas) })

$btnSim.Add_Click({
    $flags = Get-FlagsMarcadas
    if ($flags -notcontains '/L') { $flags += '/L' }
    Executar $flags
})

$btnAjuda.Add_Click({ Mostrar-Ajuda })

Update-Preview
[void]$form.ShowDialog()

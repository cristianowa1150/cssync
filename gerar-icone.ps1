# =====================================================================
#  Gera o icone do CSSync (cssync.ico + icone-256.png)
#  Desenho: pasta FONTE (amarela) -> seta -> pasta DESTINO (verde)
#  Formato: entradas BMP nao-comprimidas ate 64px (compatibilidade GDI+)
#           e PNG para 128/256px, como nos icones padrao do Windows.
#  © 2026 Cristiano Silveira Silva
# =====================================================================

Add-Type -AssemblyName System.Drawing

function New-CaminhoArredondado([single]$x, [single]$y, [single]$w, [single]$h, [single]$raio) {
    $path = New-Object System.Drawing.Drawing2D.GraphicsPath
    $d = $raio * 2
    $path.AddArc($x, $y, $d, $d, 180, 90)
    $path.AddArc($x + $w - $d, $y, $d, $d, 270, 90)
    $path.AddArc($x + $w - $d, $y + $h - $d, $d, $d, 0, 90)
    $path.AddArc($x, $y + $h - $d, $d, $d, 90, 90)
    $path.CloseFigure()
    return $path
}

function New-Pasta($g, [single]$x, [single]$y, [single]$w, [single]$h, [System.Drawing.Color]$cor, [System.Drawing.Color]$corClara) {
    # aba da pasta
    $aba = New-CaminhoArredondado $x $y ($w * 0.55) ($h * 0.30) ($h * 0.08)
    $g.FillPath((New-Object System.Drawing.SolidBrush($cor)), $aba)
    # corpo da pasta com leve gradiente
    $corpo = New-CaminhoArredondado $x ($y + $h * 0.14) $w ($h * 0.86) ($h * 0.10)
    $rect = New-Object System.Drawing.RectangleF($x, ($y + $h * 0.14), $w, ($h * 0.86))
    $brush = New-Object System.Drawing.Drawing2D.LinearGradientBrush($rect, $corClara, $cor, 90)
    $g.FillPath($brush, $corpo)
    $aba.Dispose(); $corpo.Dispose(); $brush.Dispose()
}

function New-Desenho([int]$t) {
    $bmp = New-Object System.Drawing.Bitmap($t, $t)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias

    # fundo: quadrado arredondado azul
    $fundo = New-CaminhoArredondado 0 0 $t $t ($t * 0.18)
    $rectF = New-Object System.Drawing.RectangleF(0, 0, $t, $t)
    $brushFundo = New-Object System.Drawing.Drawing2D.LinearGradientBrush(
        $rectF, [System.Drawing.Color]::FromArgb(40, 110, 190), [System.Drawing.Color]::FromArgb(18, 55, 105), 90)
    $g.FillPath($brushFundo, $fundo)

    # pasta FONTE (amarela) e pasta DESTINO (verde)
    New-Pasta $g ($t * 0.08) ($t * 0.28) ($t * 0.34) ($t * 0.44) `
        ([System.Drawing.Color]::FromArgb(235, 175, 40)) ([System.Drawing.Color]::FromArgb(255, 215, 95))
    New-Pasta $g ($t * 0.58) ($t * 0.28) ($t * 0.34) ($t * 0.44) `
        ([System.Drawing.Color]::FromArgb(45, 140, 80)) ([System.Drawing.Color]::FromArgb(95, 195, 125))

    # seta branca FONTE -> DESTINO
    $pen = New-Object System.Drawing.Pen([System.Drawing.Color]::White, ($t * 0.055))
    $pen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
    $pen.EndCap = [System.Drawing.Drawing2D.LineCap]::ArrowAnchor
    $g.DrawLine($pen, ($t * 0.40), ($t * 0.82), ($t * 0.62), ($t * 0.82))

    $pen.Dispose(); $brushFundo.Dispose(); $fundo.Dispose(); $g.Dispose()
    return $bmp
}

function Get-EntradaPng([System.Drawing.Bitmap]$bmp) {
    $ms = New-Object System.IO.MemoryStream
    $bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
    Write-Output -NoEnumerate $ms.ToArray()
}

function Get-EntradaBmp([System.Drawing.Bitmap]$bmp) {
    # Entrada ICO classica: BITMAPINFOHEADER + pixels BGRA de baixo para cima + mascara AND
    $w = $bmp.Width; $h = $bmp.Height
    $ms = New-Object System.IO.MemoryStream
    $bw = New-Object System.IO.BinaryWriter($ms)
    $bw.Write([uint32]40)            # biSize
    $bw.Write([int32]$w)             # biWidth
    $bw.Write([int32]($h * 2))       # biHeight (XOR + AND)
    $bw.Write([uint16]1)             # biPlanes
    $bw.Write([uint16]32)            # biBitCount
    $bw.Write([uint32]0)             # biCompression
    $bw.Write([uint32]($w * $h * 4)) # biSizeImage
    $bw.Write([int32]0); $bw.Write([int32]0); $bw.Write([uint32]0); $bw.Write([uint32]0)
    for ($y = $h - 1; $y -ge 0; $y--) {
        for ($x = 0; $x -lt $w; $x++) {
            $c = $bmp.GetPixel($x, $y)
            $bw.Write([byte]$c.B); $bw.Write([byte]$c.G); $bw.Write([byte]$c.R); $bw.Write([byte]$c.A)
        }
    }
    $linhaMascara = [math]::Ceiling($w / 32.0) * 4
    $bw.Write((New-Object byte[] ($linhaMascara * $h)))   # mascara AND zerada (usa o canal alfa)
    Write-Output -NoEnumerate $ms.ToArray()
}

# ----- gera as imagens -----
$tamanhos = 16, 24, 32, 48, 64, 128, 256
$imagens = New-Object 'System.Collections.Generic.List[byte[]]'
foreach ($t in $tamanhos) {
    $bmp = New-Desenho $t
    if ($t -le 64) { $imagens.Add([byte[]](Get-EntradaBmp $bmp)) }
    else           { $imagens.Add([byte[]](Get-EntradaPng $bmp)) }
    if ($t -eq 256) { $bmp.Save((Join-Path $PSScriptRoot 'icone-256.png'), [System.Drawing.Imaging.ImageFormat]::Png) }
    $bmp.Dispose()
}

# ----- monta o arquivo .ico -----
$ms = New-Object System.IO.MemoryStream
$bw = New-Object System.IO.BinaryWriter($ms)
$bw.Write([uint16]0)                  # reservado
$bw.Write([uint16]1)                  # tipo: icone
$bw.Write([uint16]$tamanhos.Count)    # quantidade de imagens
$offset = 6 + 16 * $tamanhos.Count
for ($i = 0; $i -lt $tamanhos.Count; $i++) {
    $t = $tamanhos[$i]; [byte[]]$dados = $imagens[$i]
    if ($t -ge 256) { $dim = 0 } else { $dim = $t }
    $bw.Write([byte]$dim)             # largura (0 = 256)
    $bw.Write([byte]$dim)             # altura
    $bw.Write([byte]0)                # paleta
    $bw.Write([byte]0)                # reservado
    $bw.Write([uint16]1)              # planos
    $bw.Write([uint16]32)             # bits por pixel
    $bw.Write([uint32]$dados.Length)  # tamanho dos dados
    $bw.Write([uint32]$offset)        # posicao dos dados
    $offset += $dados.Length
}
foreach ($dados in $imagens) { $bw.Write([byte[]]$dados) }

$destino = Join-Path $PSScriptRoot 'cssync.ico'
[IO.File]::WriteAllBytes($destino, $ms.ToArray())
$bw.Dispose(); $ms.Dispose()
"Icone gerado: $destino ($([math]::Round((Get-Item $destino).Length / 1KB)) KB)"

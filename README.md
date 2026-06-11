<img src="icone-256.png" width="64" align="left" alt="Ícone do Robocopy Fácil">

# Robocopy Fácil

**Interface gráfica em português para o Robocopy do Windows — backups de A para B sem decorar parâmetros.**

<br clear="left">

[![Licença: CC BY 4.0](https://img.shields.io/badge/Licen%C3%A7a-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/deed.pt-br)
![Windows 10/11](https://img.shields.io/badge/Windows-10%2F11-0078D6?logo=windows11&logoColor=white)
![PowerShell 5.1+](https://img.shields.io/badge/PowerShell-5.1%2B-5391FE?logo=powershell&logoColor=white)
![Versão](https://img.shields.io/badge/vers%C3%A3o-1.2.0-2ea44f)
![Dependências](https://img.shields.io/badge/depend%C3%AAncias-zero-success)

O **Robocopy Fácil** é um painel de controle para o `robocopy`, a ferramenta de cópia mais confiável do Windows. Ele **não copia nada por conta própria**: apenas monta o comando, mostra exatamente o que será executado e abre o console nativo com o relatório oficial do robocopy. Quem copia é o Windows — o aplicativo é só a interface.

## ✨ Recursos

- **3 modos de cópia com um clique**, cada um explicado na tela:
  - 🟢 **Atualizar backup (A → B)** — copia arquivos **novos e alterados**, pula idênticos, **não apaga nada** no destino. O botão do dia a dia.
  - 🟠 **Espelhar (A → B)** — `/MIR`: o destino fica **idêntico** à origem, inclusive apagando o que não existe mais nela. Sempre pede confirmação.
  - 🔵 **Só arquivos novos** — copia apenas o que **não existe** no destino, sem tocar em nada que já está lá.
- **19 opções do robocopy** como caixas de seleção, cada uma com explicação em português na frente
- **Simulação 100% segura** (`/L`): mostra o que seria copiado ou apagado **sem fazer nada de verdade**
- **Pré-visualização ao vivo** do comando exato antes de executar
- **Exclusões fáceis**: campos para ignorar arquivos (`/XF`) e pastas (`/XD`)
- **Cor do texto da janela de cópia** à sua escolha: verde estilo Linux (padrão), amarelo, ciano, branco e outras
- **Janela de Ajuda colorida** explicando modos, códigos de saída e dicas
- **Zero dependências**: usa apenas PowerShell + .NET, já incluídos em qualquer Windows 10/11

## 📥 Download e uso

**Opção 1 — Executável único (recomendado para usuários):**
baixe o `RobocopyFacil.exe` na [página de Releases](../../releases) e dê dois cliques. Pronto.

> ℹ️ Na primeira execução o Windows SmartScreen pode mostrar "aplicativo não reconhecido" (o executável não tem assinatura digital paga). Clique em **Mais informações → Executar assim mesmo**.

**Opção 2 — Script direto (sem executável):**
clone ou baixe este repositório e dê dois cliques em **`Iniciar - Robocopy Facil.bat`**.

## 🛡️ Segurança dos seus dados

- A pasta **FONTE (A) nunca é modificada**, em nenhum modo — o robocopy só lê dela.
- O único modo que apaga algo (e somente no destino B) é o **Espelhar** (`/MIR`), que sempre exige confirmação explícita.
- O botão **Simular** foi testado no pior cenário (simulação de espelhamento com arquivos que "seriam apagados"): nada foi copiado, alterado ou apagado — nem em A, nem em B.
- Antes do primeiro espelhamento, **simule** e leia a lista do que será feito.

## 🔧 Para desenvolvedores

| Arquivo | Função |
|---|---|
| `RobocopyFacil.ps1` | Aplicativo completo (PowerShell + Windows Forms) |
| `Iniciar - Robocopy Facil.bat` | Atalho de execução do script |
| `gerar-icone.ps1` | Gera o `robocopy-facil.ico` e o `icone-256.png` programaticamente |
| `gerar-exe.ps1` | Compila o `RobocopyFacil.exe` com o módulo [ps2exe](https://github.com/MScholtes/PS2EXE) |

Para gerar o executável:

```powershell
Install-Module ps2exe -Scope CurrentUser   # uma única vez
.\gerar-exe.ps1
```

## 🤝 Como colaborar

Contribuições são muito bem-vindas!

1. **Abra uma issue** descrevendo o problema ou a sugestão (em português ou inglês).
2. Para enviar código: faça um **fork**, crie um branch (`git checkout -b minha-melhoria`), faça as alterações e abra um **Pull Request**.
3. Diretrizes:
   - Teste qualquer mudança na montagem de comandos usando o botão **Simular (`/L`)** antes de testar cópia real;
   - Mantenha os textos da interface em **português**, com explicações claras para usuários leigos;
   - Não adicione dependências externas — o aplicativo deve continuar rodando em qualquer Windows sem instalar nada;
   - Salve o `.ps1` em **UTF-8 com BOM** (necessário para os acentos no PowerShell 5.1).

Ideias abertas: perfis salvos de origem/destino, agendamento via Agendador de Tarefas, tradução para outros idiomas.

## 📄 Licença

Este projeto está licenciado sob a [Creative Commons Atribuição 4.0 Internacional (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/deed.pt-br) — veja o arquivo [LICENSE](LICENSE).

Você pode usar, compartilhar e adaptar livremente, inclusive comercialmente, desde que dê o devido crédito a **Cristiano Silveira Silva**.

---

**© 2026 Cristiano Silveira Silva**

# clientes

Os pontos de voz do Ignis. Um cliente capta a fala, envia ao [cérebro](../cerebro/) e reproduz a resposta.

> 🚧 Ainda sem código. O cliente do PC chega na v0.

## Clientes planejados

| Cliente | Papel | Versão |
| --- | --- | --- |
| PC | Microfone e caixa de som do computador | v0 |
| Android | Conversa por voz no celular e destino dos alarmes | v3 |

## O que não mora aqui

- **Decisões e transcrição.** O cliente não interpreta pedidos. Isso é do cérebro.
- **Aparelhos da casa, ESP32 e Arduino.** Eles recebem comandos por meio dos [servidores MCP](../mcp/), e não são pontos de voz.

## Regras

- **Cada cliente é um processo separado do cérebro**, mesmo quando os dois rodam na mesma máquina.
- **O cliente detecta a palavra de ativação no próprio aparelho** e só envia áudio ao cérebro depois dela.
- **O acesso de fora de casa é só por VPN.**

Os motivos estão no [registro de decisões](../docs/decisoes.md).

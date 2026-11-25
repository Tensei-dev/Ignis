# cerebro

O orquestrador do Ignis. Recebe a fala dos [clientes](../clientes/), decide o que fazer, chama as ferramentas dos [servidores MCP](../mcp/) e devolve a resposta falada.

> 🚧 Ainda sem código. O cérebro começa na v0.

## O que mora aqui

- **Ouvir:** transcrição da fala com faster-whisper.
- **Decidir:** agente LLM, que interpreta o pedido e escolhe uma ferramenta.
- **Confirmar:** pedido de confirmação por voz antes de ações sensíveis.
- **Falar:** síntese de voz com Kokoro TTS.

## O que não mora aqui

- **Captura e reprodução de áudio.** Microfone e caixa de som são dos clientes.
- **Detecção da palavra de ativação.** O cliente detecta "Arise Ignis" e só então envia o áudio.
- **Código de integrações.** Agenda, Spotify, casa e as demais ficam em servidores MCP.

## Regras

- O agente só usa ferramentas de uma lista fechada e nunca executa nada fora dela.
- E-mails, posts e feeds são processados sem acesso às ferramentas de ação.
- O pacote importável é `ignis_cerebro`.

## Onde roda

No PC. O uso de um Raspberry Pi será reavaliado na v1. O cliente do PC é um processo separado desde a v0, para o cérebro poder mudar de máquina sem reescrita.

Os motivos estão no [registro de decisões](../docs/decisoes.md) e nos [ADRs](../docs/adr/).

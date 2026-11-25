# cerebro

O orquestrador do Ignis. Recebe a fala dos [clientes](../clientes/), decide o que fazer, chama as ferramentas dos [servidores MCP](../mcp/) e devolve a resposta falada.

> 🚧 Em construção na H02. Por enquanto, só a transcrição.

## O que mora aqui

- **Ouvir:** transcrição da fala com o faster-whisper (Whisper large-v3-turbo) na GPU, seguida da conferência do chamado: o texto precisa ter "Ignis" nas primeiras palavras.
- **Decidir:** agente LLM, que interpreta o pedido e escolhe uma ferramenta.
- **Confirmar:** pedido de confirmação por voz antes de ações sensíveis.
- **Falar:** síntese de voz com Kokoro TTS.

## O que não mora aqui

- **Captura e reprodução de áudio.** Microfone e caixa de som são dos clientes.
- **Detecção da palavra de ativação.** O cliente detecta "Ignis Arise" e só então envia o áudio.
- **Código de integrações.** Agenda, Spotify, casa e as demais ficam em servidores MCP.

## Primeiro uso

O Whisper (1,6 GB) fica em `%LOCALAPPDATA%\Ignis\modelos` e é baixado uma vez, com conferência do SHA-256 de cada arquivo:

```powershell
uv run ignis-cerebro baixar-modelos
```

As bibliotecas da NVIDIA vêm no grupo `gpu`, instalado por padrão pelo `uv sync`.

## Testar a transcrição

```powershell
uv run ignis-cerebro transcrever arquivo.wav
```

Aceita os WAVs salvos por `ignis-pc escutar --depurar` e mostra o texto, o tempo e o resultado da conferência do chamado.

## GPU ocupada

Se outro programa, como um jogo, estiver usando a GPU acima do limite, o cérebro avisa e não transcreve. O limite padrão é de 60% de uso médio nos últimos 5 s, ou menos de 300 MB de memória de vídeo livre. Para ver o uso com o jogo aberto e calibrar o limite:

```powershell
uv run ignis-cerebro gpu
```

## Regras

- O agente só usa ferramentas de uma lista fechada e nunca executa nada fora dela.
- E-mails, posts e feeds são processados sem acesso às ferramentas de ação.
- O pacote importável é `ignis_cerebro`.

## Onde roda

No PC. O uso de um Raspberry Pi será reavaliado na v1. O cliente do PC é um processo separado desde a v0, para o cérebro poder mudar de máquina sem reescrita.

Os motivos estão no [registro de decisões](../docs/decisoes.md) e nos [ADRs](../docs/adr/).

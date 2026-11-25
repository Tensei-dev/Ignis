# Jarvis

![Status](https://img.shields.io/badge/status-em%20desenvolvimento-orange)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![MCP](https://img.shields.io/badge/protocolo-MCP-6f42c1)
![Licença](https://img.shields.io/badge/licen%C3%A7a-MIT-green)

Assistente pessoal por voz que roda em casa. Ele ouve, decide e age nos meus aparelhos e serviços, com foco em **baixa latência**, **privacidade** e **segurança**.

> 🚧 **Em desenvolvimento.** Ainda não tem uma versão utilizável. O progresso está no [roadmap](#roadmap).

## Sumário

- [O que ele faz](#o-que-ele-faz)
- [Como funciona](#como-funciona)
- [Arquitetura](#arquitetura)
- [Princípios](#princípios)
- [Stack](#stack)
- [Hardware](#hardware)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Roadmap](#roadmap)
- [Como rodar](#como-rodar)
- [Licença](#licença)

## O que ele faz

| Recurso | Descrição | Versão |
| --- | --- | --- |
| 🎙️ Conversa por voz | No PC e no celular Android, ativado por "hey Jarvis" | v0 / v3 |
| 🛒 Lista de mercado | Adiciona e remove itens por voz e diz o que está faltando com mais urgência | v0 |
| 💸 Contas a pagar | Lembra antes do vencimento e no dia | v0 |
| 💡 Casa conectada | Controla a lâmpada e avisa quando a ração dos gatos está baixa | v1 |
| ⏰ Despertador | Cria alarmes no celular por comando de voz | v3 |
| 📅 Agenda | Consulta e marca compromissos no Google Agenda | v3 |
| 🎵 Música | Toca minhas playlists no Spotify | v3 |
| ☀️ Resumo da manhã | Agenda do dia, contas, mercado urgente e destaques de leitura (Medium e newsletters), narrados em até 2 minutos | v3 |
| 🔧 Plataforma de comandos | Controla aparelhos que eu mesmo construo com ESP32 e Arduino via MQTT | v4 |

## Como funciona

Um comando passa por estas etapas:

1. **Ativação:** o cliente detecta "hey Jarvis" no próprio aparelho e só então envia o áudio ao cérebro. No PC, quem detecta é o openWakeWord.
2. **Ouvir:** o faster-whisper transcreve a fala.
3. **Decidir:** o agente LLM interpreta o pedido e escolhe uma ferramenta da lista permitida.
4. **Confirmar:** se a ação for sensível, o Jarvis pede confirmação por voz antes de seguir.
5. **Agir:** a ferramenta é chamada no servidor MCP correspondente.
6. **Falar:** o Kokoro TTS narra a resposta.

Exemplos:

```text
"Hey Jarvis, coloca leite e café na lista."
"Hey Jarvis, quais contas vencem esta semana?"
"Hey Jarvis, apaga a luz da sala."
"Hey Jarvis, me acorda às 6 e meia."
```

## Arquitetura

```mermaid
flowchart TD
    PC[PC: microfone e caixa de som] --> Brain
    Phone[Celular Android] --> Brain
    subgraph Brain[Cérebro: orquestrador no Raspberry Pi]
        STT[Ouvir: faster-whisper] --> Agent[Agente LLM]
        Agent --> TTS[Falar: Kokoro TTS]
    end
    Agent -- MCP --> Tasks[Tarefas: mercado e contas]
    Agent -- MCP --> HA[Home Assistant: lâmpada, ração, despertador]
    Agent -- MCP --> Cal[Google Agenda]
    Agent -- MCP --> Spotify[Spotify]
    Agent -- MCP --> Reads[Leituras: RSS e Gmail]
    Agent -- MCP --> MQTT[MQTT: ESP32 e Arduino]
```

- O **Raspberry Pi** fica ligado 24 h e coordena tudo.
- O **LLM roda na GPU do PC** com vLLM. Uma API externa serve de reserva quando o PC está desligado.
- **Cada integração é um servidor MCP separado**, então trocar um serviço ou o modelo não mexe no resto.

## Princípios

- **Age só por ações validadas.** O agente tem uma lista fechada de ferramentas e nunca executa nada fora dela.
- **Conteúdo lido não dá ordens.** E-mails, posts e feeds são processados sem acesso às ferramentas de ação, como proteção contra prompt injection.
- **Confirma o que importa.** Ações sensíveis pedem confirmação por voz.
- **Privacidade por padrão.** A palavra de ativação é detectada localmente, e nada fica exposto direto na internet: o acesso externo é só por VPN.
- **Guiado por avaliação.** Uma suíte de comandos com as ações esperadas roda no CI a cada mudança.
- **Latência como meta.** Objetivo: menos de 1 s entre o fim da fala e o início da resposta.

## Stack

| Camada | Tecnologias |
| --- | --- |
| Voz | faster-whisper, openWakeWord, Kokoro TTS |
| Agente | Python, MCP, vLLM (modelo aberto quantizado) |
| Dados | PostgreSQL |
| Casa | Home Assistant (integração Tuya), MQTT (Mosquitto), ESP32 |
| Infra | Raspberry Pi 5, Docker, Tailscale, GitHub Actions |
| Integrações | Google Agenda, Spotify Web API, Gmail API (só leitura), RSS |

## Hardware

| Peça | Papel |
| --- | --- |
| Raspberry Pi 5 | Orquestrador ligado 24 h, servidores MCP, PostgreSQL e Home Assistant |
| PC com GPU NVIDIA | Roda o LLM local com vLLM, além do microfone e da caixa de som |
| Celular Android | Segundo ponto de voz e destino dos alarmes |
| Lâmpada e alimentador Tuya | Aparelhos da casa controlados pelo Home Assistant |
| ESP32 / Arduino | Aparelhos próprios conectados via MQTT |

## Estrutura do repositório

```text
jarvis/
├── cerebro/          # Orquestrador: STT, agente e TTS
├── mcp/              # Um servidor MCP por integração, cada um como pacote próprio
├── clientes/         # Pontos de voz (PC e Android): palavra de ativação e áudio
└── docs/             # Documentação, registro de decisões e ADRs
```

Cada pasta principal tem um README explicando o que mora nela.

Convenções:

- O código e a documentação são escritos em português do Brasil.
- Nomes de código e de arquivos não levam acento nem cedilha.
- O código segue a PEP 8.
- A pasta `mcp/` não tem `__init__.py`. Cada servidor usa o layout `src/` para não conflitar com o SDK `mcp`.

O cliente do PC é um processo separado do cérebro desde a v0. Na v1, o cérebro muda para o Raspberry Pi sem precisar ser reescrito.

As decisões tomadas até aqui estão em [`docs/decisoes.md`](docs/decisoes.md).

## Roadmap

- [ ] **v0: Jarvis no PC.** Voz, ferramentas, lista de mercado e contas
- [ ] **v1: Casa conectada.** Raspberry Pi, Home Assistant, lâmpada e alimentador
- [ ] **v2: Cérebro próprio.** LLM local na GPU, avaliação, segurança e latência abaixo de 1 s
- [ ] **v3: Assistente completo.** App Android, despertador, agenda, Spotify e resumo da manhã
- [ ] **v4: Plataforma de comandos.** MQTT e nós ESP32

## Como rodar

> Em breve. As instruções entram aqui junto com a v0.

## Licença

Distribuído sob a licença MIT.

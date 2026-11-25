# ADR 0002: Um servidor MCP por integração

**Status:** Aceito (2026-11-24)

## Contexto

O Jarvis conversa com serviços muito diferentes: lista de mercado e contas, Home Assistant, Google Agenda, Spotify, RSS, Gmail e aparelhos via MQTT. Cada um tem as próprias bibliotecas, credenciais e falhas.

O agente também precisa seguir dois princípios do projeto: só agir por uma lista fechada de ferramentas e ler conteúdo externo sem acesso às ferramentas de ação. Com tudo num programa só, esses limites ficariam misturados no mesmo código.

## Decisão

Cada integração é um servidor MCP separado, que expõe as suas ferramentas ao cérebro. O cérebro não contém código de integrações.

Cada servidor é um pacote próprio dentro de `mcp/`, no layout `src/`, com as suas dependências e os seus testes. O nome importável leva o prefixo `jarvis_`.

## Consequências

**Positivas**

- Trocar um serviço ou o modelo não mexe no resto.
- As credenciais de um serviço podem ficar só no servidor que as usa.
- A falha de um servidor não precisa derrubar os outros.
- Cada servidor pode ser testado e empacotado sozinho.

**Negativas**

- Há mais processos para iniciar, monitorar e atualizar.
- Cada chamada passa por uma camada a mais, o que conta para a meta de latência.
- Separar os servidores não aplica sozinho os princípios de segurança. A lista fechada e o isolamento do conteúdo lido precisam ser implementados no cérebro e cobertos por testes.

## Relacionado

- [D02, D08, D09 e D21](../decisoes.md) no registro de decisões.

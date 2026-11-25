# mcp

Os servidores MCP do Ignis, um por integração. Cada um expõe ao [cérebro](../cerebro/) as ferramentas de um serviço, e pode ser trocado sem mexer no resto.

> 🚧 Ainda sem código. O primeiro servidor, o de tarefas, chega na v0.

## Servidores planejados

| Integração | O que faz | Versão |
| --- | --- | --- |
| Tarefas | Lista de mercado e contas a pagar | v0 |
| Casa | Lâmpada e ração dos gatos (v1) e despertador (v3), via Home Assistant | v1 / v3 |
| Agenda | Consulta e marca compromissos no Google Agenda | v3 |
| Spotify | Toca playlists | v3 |
| Leituras | Destaques de RSS e Gmail, só leitura | v3 |
| MQTT | Aparelhos próprios com ESP32 e Arduino | v4 |

## Como um servidor é organizado

Cada servidor é um pacote próprio, com as suas dependências e os seus testes:

```text
mcp/
└── tarefas/
    ├── pyproject.toml
    ├── src/
    │   └── ignis_tarefas/
    │       └── __init__.py
    └── tests/
```

## Regras

- **A pasta `mcp/` não tem `__init__.py`.** O SDK oficial também se chama `mcp`, e um `__init__.py` aqui poderia fazer o Python importar esta pasta no lugar dele.
- **O pacote importável leva o prefixo `ignis_`**, para não conflitar com bibliotecas de mesmo nome.
- **O conteúdo lido não dá ordens.** O que vem de e-mails, posts e feeds é processado sem acesso às ferramentas de ação.

Os motivos estão no [registro de decisões](../docs/decisoes.md).

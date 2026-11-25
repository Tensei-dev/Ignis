# Registro de decisões

Log das decisões tomadas em cada tarefa, da mais antiga para a mais recente. As decisões de arquitetura também ganham um ADR em [`docs/adr/`](adr/).

## H01: Estrutura inicial do projeto

### T01: Criar repositório (core/, mcp/, clients/) com README

**D01 · 2026-11-23 · Idioma do repositório: PT-BR**
Todo o repositório usa português do Brasil, código incluído: nomes de pastas, módulos, variáveis, funções, comentários, commits e documentação.
*Motivo:* escolha do autor para a fase inicial do projeto. Pode ser revista mais tarde.

**D02 · 2026-11-23 · Servidores MCP com layout `src/` dentro de `mcp/`**
A pasta `mcp/` fica com esse nome e **não** tem `__init__.py`. Cada servidor é um pacote próprio no layout `src/`, por exemplo `mcp/tarefas/src/jarvis_tarefas/`.
*Motivo:* o SDK oficial de MCP para Python também se chama `mcp`. Se `mcp/` fosse um pacote e a raiz do repositório entrasse no `sys.path` (`python -m` ou pytest), o `import mcp` carregaria a pasta local no lugar do SDK. Com o layout `src/`, cada pacote só pode ser importado depois de instalado, o que evita esse conflito.

**D03 · 2026-11-23 · Nomes das pastas principais**
`mcp/` mantém o nome, porque é o nome do protocolo. As demais pastas principais ficam em português: `clients/` vira `clientes/` e `core/` vira `cerebro/` (sem acento, como pede a D04).
*Motivo:* consequência da D01. "Cérebro" é como o projeto já chama o orquestrador.

**D04 · 2026-11-23 · Convenções de nomes no código**
- Nomes de código e de arquivos sem acento e sem cedilha (`cerebro`, `configuracao`). Acentos são permitidos em comentários, docstrings, mensagens e documentação.
- Seguir a PEP 8: funções, variáveis, módulos e pacotes em `snake_case`, classes em `PascalCase` e constantes em `MAIUSCULAS_COM_SUBLINHADO`.

*Motivo:* acentos em pacotes, módulos e arquivos dão problema com ferramentas (uv, Docker) e com sistemas de arquivos diferentes (Windows e Linux).

**D05 · 2026-11-23 · Cliente do PC separado do cérebro desde a v0**
O cliente do PC (microfone e caixa de som) é um processo separado do cérebro desde a v0, mesmo com os dois rodando na mesma máquina.
*Motivo:* na v1 o cérebro vai para o Raspberry Pi sem reescrever nada. A contrapartida é definir já na v0 como o cliente manda áudio para o cérebro e recebe a resposta.

**D06 · 2026-11-23 · Documentação: README por pasta e site no GitHub Pages**
Cada pasta principal tem um README curto explicando o que mora ali. Mais tarde, a documentação do projeto vai ser publicada no GitHub Pages.
*Motivo:* quem cai numa pasta pelo GitHub entende o contexto na hora. O site reúne tudo num lugar só.

**D17 · 2026-11-24 · Palavra de ativação detectada no cliente**
Cada cliente detecta "hey Jarvis" no próprio aparelho e só envia áudio ao cérebro depois da ativação. O cérebro não recebe áudio contínuo.
*Motivo:* com o cliente separado do cérebro (D05), detectar no cérebro exigiria transmitir o microfone o tempo todo. No cliente, há mais privacidade e menos uso de rede. A contrapartida é que cada cliente precisa da própria detecção: o openWakeWord passa a ser dependência do cliente do PC, e o app Android (v3) vai precisar de uma solução própria.

### T02: Ambiente Python com uv, ruff, pytest e pre-commit

**D07 · 2026-11-23 · Python 3.12**
A versão do Python fica fixada em `.python-version` e é instalada pelo uv.
*Motivo:* as libs de voz (faster-whisper, openWakeWord, Kokoro) dependem de wheels compilados e costumam demorar a dar suporte às versões novas do Python. Se todas tiverem wheel para a 3.13, dá para subir.

**D08 · 2026-11-23 · Workspace do uv com um lock só**
O `pyproject.toml` da raiz define um workspace com os membros `cerebro`, `mcp/*` e `clientes/*`. O repositório tem um único `uv.lock`, e cada parte instala só o que precisa com `uv sync --package <nome>`.
*Motivo:* versões iguais em todo o projeto e imagens Docker enxutas por servidor. Se dois membros um dia precisarem de versões incompatíveis da mesma lib, o membro em conflito sai do workspace.

**D09 · 2026-11-23 · Prefixo `jarvis_` nos nomes importáveis**
As pastas têm nomes curtos (`mcp/agenda/`), mas os pacotes levam o prefixo (`jarvis_agenda`, `jarvis_cerebro`).
*Motivo:* evitar conflito com bibliotecas de mesmo nome (`spotify`, `agenda`), o mesmo problema que a D02 resolve.

**D10 · 2026-11-23 · Testes dentro de cada pacote, com `--import-mode=importlib`**
Cada membro do workspace tem a própria pasta `tests/`. Tudo roda da raiz com `uv run pytest`, e o pytest usa `--import-mode=importlib`.
*Motivo:* os testes ficam perto do código que testam. O modo `importlib` não mexe no `sys.path`, o que evita o conflito da D02, e aceita arquivos de teste com o mesmo nome em pacotes diferentes.

**D11 · 2026-11-23 · Hooks do pre-commit sem testes**
Os hooks são: ruff (lint com `--fix` e formatação), os hooks básicos do `pre-commit-hooks` (espaços no fim da linha, fim de arquivo, YAML/TOML válidos, arquivos grandes) e o `uv-lock`. Os testes não entram, e a detecção de segredos fica para a T05.
*Motivo:* o commit precisa ser rápido, ou o hook vira algo que se pula com `--no-verify`. Os testes rodam no CI (T03).

**D12 · 2026-11-23 · Ferramentas no grupo `dev` da raiz**
`pytest`, `ruff` e `pre-commit` ficam no grupo `dev` do `pyproject.toml` da raiz e valem para todos os membros.
*Motivo:* as ferramentas ficam fora das instalações de produção (`uv sync --no-dev`).

**D13 · 2026-11-23 · Regras do ruff**
O ruff faz o lint e a formatação, com a configuração no `pyproject.toml` da raiz e linhas de até 88 caracteres. Famílias de regras ativas:
- `E` (pycodestyle) e `F` (Pyflakes);
- `I` (ordem dos imports) e `N` (nomes PEP 8);
- `UP` (sintaxe moderna) e `B` (armadilhas comuns);
- `PLC2401` e `PLC2403` (nomes e imports sem caracteres não ASCII).

*Motivo:* pegar bugs cedo, manter o código padronizado e verificar automaticamente as convenções da D04. Com a família `E` completa entra a E501 (linha longa), que às vezes pede quebra de linha manual.

**D14 · 2026-11-23 · Checagem de tipos adiada**
mypy, pyright e ty ficam fora da H01. Voltam numa tarefa futura, quando houver código suficiente para valer a pena.

**D15 · 2026-11-23 · Quebras de linha em LF, garantidas pelo `.gitattributes`**
Todo arquivo de texto é guardado e extraído com LF (`\n`), por meio de um `.gitattributes` na raiz. A exceção são os scripts que só rodam no Windows (`.bat`, `.cmd`), que ficam com CRLF. Arquivos binários (modelos, áudio, imagens) são marcados explicitamente como binários.
*Motivo:* o desenvolvimento é no Windows (CRLF), mas o código roda no Raspberry Pi e no Docker (Linux, LF). Arquivos com CRLF quebram scripts e configurações no Linux. Resolver no `.gitattributes`, em vez de num hook do pre-commit, vale para qualquer clone e não depende de ferramenta instalada. Essa regra também sobrepõe o `core.autocrlf=true`, que o Git for Windows ativa por padrão.

**D16 · 2026-11-23 · `.vscode/settings.json` versionado**
As configurações do VS Code para o projeto ficam no git: LF, linha em branco no fim do arquivo, remoção de espaços no fim da linha e o ruff como formatador ao salvar. Nada específico de uma máquina entra no arquivo, como caminhos de interpretador.
*Motivo:* quem clonar o projeto ganha o mesmo comportamento do editor, e os hooks do pre-commit quase nunca precisam corrigir nada.

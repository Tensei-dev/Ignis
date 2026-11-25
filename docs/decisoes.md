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

### T03: CI no GitHub Actions rodando lint e testes

**D18 · 2026-11-24 · CI em pull requests e em pushes na `main`**
O workflow roda em todo pull request e em todo push na `main`.
*Motivo:* pegar problemas antes do merge e confirmar o estado da `main` depois dele.

**D19 · 2026-11-24 · Dois jobs: `lint` e `testes`**
O job `lint` roda `pre-commit run --all-files`. O job `testes` roda o pytest em todos os pacotes do workspace.
*Motivo:* o `lint` repete os mesmos hooks do commit local, nas mesmas versões, sem duplicar a lista no workflow.

**D20 · 2026-11-24 · Versão do uv fixada no `pyproject.toml`**
A versão do uv fica em `[tool.uv] required-version`, no `pyproject.toml` da raiz.
*Motivo:* a mesma regra vale para o ambiente local e para o CI, escrita em um lugar só.

**D21 · 2026-11-24 · Testes isolados por pacote a partir do segundo pacote**
Quando existir o segundo pacote do workspace, o CI passa a testar cada um num ambiente só com as dependências dele:

```bash
uv export --locked --only-group dev -o dev-req.txt
uv run --isolated --locked --package <nome> --with-requirements dev-req.txt pytest <pasta>
```

*Motivo:* no ambiente completo, um pacote pode usar sem querer uma lib que só outro declarou, e o erro só apareceria no Docker. Com um pacote só, o teste isolado não acrescenta nada.

**D22 · 2026-11-24 · Testes em Linux e Windows, lint só em Linux**
O job `testes` roda nos dois sistemas, e o `lint` roda só em Linux. Os testes não dependem de microfone nem de caixa de som: usam áudio falso.
*Motivo:* o cérebro vai rodar em Linux (Raspberry Pi e Docker) e o cliente do PC roda em Windows. O resultado do lint não deveria depender do sistema.

**D23 · 2026-11-24 · `--locked` no CI**
O CI usa `--locked` e falha se o `uv.lock` não corresponder aos `pyproject.toml`.
*Motivo:* sem isso, o CI geraria um lock temporário e aprovaria versões diferentes das que estão no repositório.

**D24 · 2026-11-24 · CI com permissão mínima e actions fixadas por SHA**
O `GITHUB_TOKEN` do workflow tem só `contents: read`, e cada action é fixada pelo SHA do commit.
*Motivo:* limitar o estrago se uma action ou dependência for comprometida. Uma tag pode ser movida para outro código, e um SHA não.

**D25 · 2026-11-24 · Repositório público e `main` protegida**
O repositório passa a ser público, e a `main` só recebe mudanças por pull request com o CI verde. Não é exigida a aprovação de outra pessoa.
*Motivo:* sem bloqueio, o CI só avisa depois que o código já entrou. No plano gratuito do GitHub, a proteção de branch só existe em repositórios públicos. A contrapartida é que todo o histórico fica visível.

**D26 · 2026-11-24 · Histórico publicado sem reescrita**
Os commits existentes vão para o repositório público como estão, com a identidade de autor original.
*Motivo:* escolha do autor. A verificação do histórico não encontrou segredos nos arquivos.

**D27 · 2026-11-24 · Licença GPL-3.0-or-later**
O código do Jarvis é distribuído sob a GPL, versão 3 ou posterior, no lugar da MIT prevista no início. O texto completo fica no arquivo `LICENSE`, na raiz.
*Motivo:* quem distribuir uma versão modificada precisa abrir o código também. A contrapartida é que o código não pode ser incorporado a um produto fechado distribuído a terceiros. Bibliotecas e modelos mantêm as próprias licenças.

### T04: Registrar decisões de arquitetura (ADR)

**D28 · 2026-11-24 · ADRs em `docs/adr/`, no formato de Nygard**
Cada decisão de arquitetura ganha um arquivo numerado com contexto, decisão e consequências. Um ADR aceito não é reescrito: se a decisão mudar, outro o substitui. Os primeiros tratam do [PC como central](adr/0001-pc-como-central.md) (0001), de [um servidor MCP por integração](adr/0002-um-servidor-mcp-por-integracao.md) (0002) e do [cliente separado do cérebro](adr/0003-cliente-separado-do-cerebro.md) (0003).
*Motivo:* preservar o raciocínio das decisões que custam caro para desfazer.

**D29 · 2026-11-24 · Começar só pelo PC, ligado 24 h**
As primeiras implementações são todas no computador, que fica ligado 24 h. O smartphone fica para depois. O PC tem uma RTX 4060 com 8 GB de VRAM.
*Motivo:* escolha do autor para a fase inicial. Com o PC sempre ligado, o processamento pesado pode contar com a GPU.

**D30 · 2026-11-24 · PC como central, Pi reavaliado na v1**
O cérebro, os servidores MCP e o cliente rodam no PC. O Raspberry Pi é reavaliado na v1, com medições. O raciocínio está no [ADR 0001](adr/0001-pc-como-central.md). Onde as decisões anteriores dizem que o cérebro vai para o Pi na v1 (D05, D22), passa a valer esta.
*Motivo:* com o PC ligado 24 h, o motivo principal para começar pelo Pi enfraqueceu.

**D31 · 2026-11-24 · LLM local com vLLM desde a v0**
O LLM roda na GPU do PC com vLLM desde a v0, e não só na v2.
*Motivo:* escolha do autor. A contrapartida é que o vLLM não roda direto no Windows e exige o WSL, e que os 8 GB de VRAM são divididos com a transcrição e com jogos.

**D32 · 2026-11-24 · API do Claude na v0, no lugar do vLLM**
Substitui a D31. Na v0, o cérebro usa a API do Claude, com o SDK oficial, e o LLM local volta para a v2. Só um módulo conhece o Claude: o resto do cérebro usa uma interface própria. O agente e o controle das ferramentas ficam no cérebro.
*Motivo:* o vLLM não roda direto no Windows e disputaria os 8 GB de VRAM com jogos. A contrapartida é o custo por uso, a dependência da internet e o envio do texto das conversas a um serviço externo.

**D33 · 2026-11-24 · Claude Haiku 5.5 como modelo inicial**
O modelo da v0 é o `claude-haiku-5-5`. Se ele errar a escolha das ferramentas, o próximo passo é testar o Sonnet ou o Opus.
*Motivo:* os comandos da v0 são simples, e o Haiku é o modelo atual mais barato.

**D34 · 2026-11-24 · Regras para o texto enviado à API do Claude**
O texto das conversas pode ser enviado à API do Claude na v0, com estas regras:
- o áudio não sai de casa, e a transcrição é local;
- nada é enviado antes da palavra de ativação;
- o cérebro envia só o necessário para cada pedido, e não o histórico inteiro;
- segredos e senhas nunca entram no texto;
- e-mails e agenda só são enviados depois de uma nova decisão, na v3.

*Motivo:* pela política consultada em 2026-11-24, a Anthropic não treina modelos com o conteúdo da API por padrão e o apaga em até 30 dias, com exceções, como conteúdo sinalizado por segurança (até 2 anos). As regras reduzem o que sai de casa.

### T05: Segredos em `.env` com `.env.example`

**D35 · 2026-11-24 · Um `.env` por processo, com `.env.example` versionado**
Cada programa tem o próprio `.env`, fora do git, e um `.env.example` só com os nomes, como em `cerebro/`.
*Motivo:* cada processo tem acesso só às próprias chaves, como prevê o [ADR 0002](adr/0002-um-servidor-mcp-por-integracao.md).

**D36 · 2026-11-24 · Leitura de segredos com `pydantic-settings`**
O código lê o `.env` com `pydantic-settings` e guarda as chaves como `SecretStr`. Entra com o primeiro código do cérebro.
*Motivo:* o programa falha logo ao iniciar se faltar uma chave, e a chave não aparece por engano em logs e mensagens.

**D37 · 2026-11-24 · Detecção de segredos em três camadas**
- No commit, o hook do gitleaks verifica o que está no stage.
- No CI, o job `lint` varre todo o histórico com o gitleaks.
- No GitHub, ficam ativos o Secret scanning e o Push protection.

*Motivo:* o hook do commit só olha o stage e pode ser pulado com `--no-verify`. Num teste, ele não acusou uma chave já commitada, e a varredura do histórico acusou.

**D38 · 2026-11-24 · Chave única do Jarvis, com limite de gasto, e revogação imediata se vazar**
O Jarvis usa uma chave de API só dele, com limite de gasto no Console. Se uma chave vazar, o primeiro passo é revogá-la, e só depois limpar o repositório.
*Motivo:* o repositório é público, e apagar a chave num commit seguinte não a remove do histórico.

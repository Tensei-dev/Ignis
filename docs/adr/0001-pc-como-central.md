# ADR 0001: PC como central, com o Raspberry Pi reavaliado na v1

**Status:** Aceito (2026-11-24)

## Contexto

O plano inicial previa o Raspberry Pi 5 como orquestrador ligado 24 h, com o LLM na GPU do PC. O Pi garantiria que o Jarvis funcionasse com o PC desligado.

O PC passou a ficar ligado 24 h e tem uma RTX 4060 com 8 GB de VRAM, e as primeiras implementações são todas nele. Com isso, o motivo principal para começar pelo Pi enfraqueceu. O PC também é usado para jogos e outros programas que ocupam a GPU.

A meta é começar a responder em menos de 1 s depois do fim da fala.

Alternativas consideradas:

- **Pi como central:** o Pi coordena e a GPU do PC processa. São duas máquinas para manter desde o início, e mais rede em cada pedido.
- **PC como central, sem o Pi:** mais simples, mas descarta o Pi sem medições.

## Decisão

O PC é a central do Jarvis: nele rodam o cérebro, os servidores MCP e o cliente de voz.

O uso do Raspberry Pi é reavaliado na v1, com as medições de latência da v0 e as necessidades do Home Assistant e dos lembretes. O cérebro continua um processo separado do cliente ([ADR 0003](0003-cliente-separado-do-cerebro.md)), para poder mudar de máquina.

## Consequências

**Positivas**

- Uma máquina só para configurar e manter na v0.
- Não há rede entre o cérebro e a GPU.
- A decisão sobre o Pi pode ser tomada com medições.

**Negativas**

- Se o PC reiniciar, travar ou for desligado, o Jarvis para, inclusive os lembretes.
- Um PC ligado 24 h gasta mais energia que um Raspberry Pi.
- Jogos e outros programas disputam a GPU com o Jarvis, o que pode aumentar a latência ou deixar o modelo indisponível.
- O cérebro precisa evitar dependências exclusivas do Windows, ou a mudança de máquina deixa de ser simples.

## Relacionado

- [D05, D29 e D30](../decisoes.md) no registro de decisões.

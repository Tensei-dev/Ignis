# ADR 0003: Cliente separado do cérebro, com ativação no cliente

**Status:** Aceito (2026-11-24)

## Contexto

O Jarvis precisa de um ponto de voz, com microfone e caixa de som, e de um cérebro, que transcreve, decide, age e responde. Na v0, os dois rodam no mesmo computador. Mais tarde, podem ficar em máquinas diferentes, e outros pontos de voz podem surgir.

Também é preciso escolher quem detecta "hey Jarvis". Com o cliente e o cérebro separados, detectar no cérebro exigiria transmitir o microfone o tempo todo.

## Decisão

O cliente e o cérebro são processos separados desde a v0, mesmo na mesma máquina.

O cliente capta a fala, detecta a palavra de ativação no próprio aparelho, envia o áudio ao cérebro só depois dela e reproduz a resposta. O cérebro transcreve, decide, chama as ferramentas e gera a voz da resposta.

## Consequências

**Positivas**

- O cérebro pode mudar de máquina sem reescrever o cliente.
- Um novo ponto de voz não exige mudar o que o cérebro decide.
- O áudio anterior à ativação não sai do aparelho, e a rede é menos usada.

**Negativas**

- A comunicação entre os dois precisa ser definida já na v0 e soma latência.
- Há dois processos para iniciar e acompanhar.
- Cada tipo de cliente precisa da própria detecção. O openWakeWord atende o cliente do PC, e um aplicativo Android precisaria de outra solução.

## Em aberto

- Como o cliente envia o áudio ao cérebro e recebe a resposta.

## Relacionado

- [D05, D17 e D22](../decisoes.md) no registro de decisões.

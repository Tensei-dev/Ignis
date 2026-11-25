# pc

O cliente de voz do Ignis no computador. Escuta o microfone o tempo todo, detecta "Ignis Arise", envia o pedido ao [cérebro](../../cerebro/) e toca a resposta.

> 🚧 Em construção na H02.

## Como funciona

1. **Escuta contínua.** Antes da ativação, só os últimos 2 s de áudio ficam na memória e são descartados continuamente.
2. **Ativação.** O sherpa-onnx detecta "Ignis Arise", com frases parecidas como iscas. Palmas antes da frase são opcionais.
3. **Pedido.** A gravação segue até 0,8 s de silêncio, com limite de 30 s.
4. **Envio.** O cliente envia ao cérebro os 2 s guardados, com a frase, e o pedido. O cérebro confere se a voz é a cadastrada e se a transcrição começa com "Ignis".
5. **Resposta.** A escuta fica pausada enquanto o Ignis fala e continua por mais 5 s sem exigir a frase de novo.

## Regras

- **O áudio nunca é gravado em disco**, exceto em modo de depuração, fora do git.
- **Há um modo mudo**, para chamadas e jogos.
- **O microfone é escolhido pelo nome**, com o padrão do Windows como reserva.
- **Os modelos de voz não vão para o git.** Ficam numa pasta `modelos/`, baixados por um comando.
- **Microfone e alto-falante ficam atrás de interfaces**, para os testes rodarem no CI sem hardware de áudio.
- O pacote importável é `ignis_pc`.

Os motivos estão no [registro de decisões](../../docs/decisoes.md) (D17, D41 a D47).

# Testes pendentes

Testes manuais que só podem ser feitos com o microfone, a voz, o PC e os jogos do autor. Até aqui, a escuta, a ativação e a transcrição foram validadas com voz sintética.

Marque cada item quando fizer e anote o resultado. O que sair diferente do esperado vira uma decisão ou uma correção.

## 1. Escuta com o microfone real

```powershell
uv run ignis-pc escutar --depurar
```

| Feito | Cenário | Esperado |
| --- | --- | --- |
| [ ] | "Ignis, que horas são", com o PC em uso | Chamado (nome) e um pedido |
| [ ] | Logo depois, outro pedido **sem** o nome | Pedido pela conversa |
| [ ] | "Ignis", uma pausa para pensar, e o pedido | Um pedido só, com tudo |
| [ ] | "Ignis Arise" sozinho | Chamado sem pedido (D60) |
| [ ] | Conversar normalmente por alguns minutos, sem chamar | Nenhum evento |
| [ ] | Pausa de 1 s no meio do pedido | O pedido é cortado na pausa (D57) |
| [ ] | Barulho repentino, como bater na mesa, no meio do pedido | Pode encerrar o pedido antes da hora (D57) |
| [ ] | PC bloqueado (Win+L): "Ignis, que horas são" | Ignorado |
| [ ] | PC bloqueado (Win+L): "Ignis Arise, que horas são" | Chamado (frase) e um pedido |

Resultado:

## 2. Bloqueio da sessão

O Ignis nunca foi testado com o PC bloqueado de verdade. Rode, aperte **Win+L** em seguida e desbloqueie depois de uns 20 s:

```powershell
uv run python -c "import time; from ignis_pc.sessao import SessaoWindows as S; time.sleep(15); s=S(); print('bloqueado:', s.bloqueado())"
```

- [ ] Esperado: `bloqueado: True` (D54).

Resultado:

## 3. Limite de GPU com um jogo aberto

```powershell
uv run ignis-cerebro gpu
```

- [ ] Abrir um jogo e anotar a média de uso. O limite de 60% (D63) é um palpite e deve ficar entre o uso normal do PC e o uso do jogo.

Resultado:

Pergunta em aberto: liberar a memória de vídeo do Whisper (1,1 GB) quando a GPU ficar ocupada por um tempo, e carregá-lo de novo depois (cerca de 4 s no primeiro pedido).

## 4. Transcrição da voz real

Com os WAVs gravados no item 1:

```powershell
uv run ignis-cerebro transcrever "$env:LOCALAPPDATA\Ignis\depuracao\pedido_<data>_<origem>.wav"
```

- [ ] Conferir se o texto está certo e como o Whisper escreve "Ignis" com a sua voz e o headset. Se aparecer uma grafia nova, ela entra nas variantes da conferência (D64).
- [ ] Apagar os WAVs de `%LOCALAPPDATA%\Ignis\depuracao` depois: eles guardam a sua voz.

Resultado:

## 5. Frase de ativação com outro microfone

- [ ] Ao trocar o headset, repetir o teste de "Ignis Arise" e "Igris Arise" (10 vezes cada) e a escuta do item 1 de longe, a 2 ou 3 metros (D47).

Resultado:

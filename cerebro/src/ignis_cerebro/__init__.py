"""Cérebro do Ignis."""

import argparse
import logging
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ignis-cerebro", description="Cérebro do Ignis."
    )
    comandos = parser.add_subparsers(dest="comando", required=True)
    comandos.add_parser("baixar-modelos", help="Baixa e confere os modelos do cérebro.")
    transcrever = comandos.add_parser(
        "transcrever",
        help="Transcreve WAVs, como os salvos por `ignis-pc escutar --depurar`.",
    )
    transcrever.add_argument("arquivos", nargs="+", type=Path)
    gpu = comandos.add_parser(
        "gpu", help="Mostra o uso da GPU a cada segundo, para calibrar o limite."
    )
    gpu.add_argument(
        "--limite", type=float, default=60.0, help="Porcentagem (padrão: 60)."
    )
    argumentos = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logging.getLogger("faster_whisper").setLevel(logging.WARNING)

    if argumentos.comando == "baixar-modelos":
        return _baixar_modelos()
    if argumentos.comando == "transcrever":
        return _transcrever(argumentos.arquivos)
    if argumentos.comando == "gpu":
        return _gpu(argumentos.limite)
    return 0


def _baixar_modelos() -> int:
    from ignis_cerebro.modelos import TODOS, ErroDeModelo, baixar

    for modelo in TODOS:
        try:
            baixar(modelo)
        except (ErroDeModelo, OSError) as erro:
            logging.error("%s", erro)
            return 1
    return 0


def _transcrever(arquivos: list[Path]) -> int:
    from ignis_cerebro.conferencia import conferir_chamado
    from ignis_cerebro.gpu import MonitorDeGpu, leitor_nvml
    from ignis_cerebro.modelos import WHISPER_TURBO, caminho, esta_baixado
    from ignis_cerebro.transcricao import GpuOcupada, TranscritorWhisper, ler_wav

    if not esta_baixado(WHISPER_TURBO):
        logging.error("Modelo não baixado. Rode `uv run ignis-cerebro baixar-modelos`.")
        return 1
    monitor = MonitorDeGpu(leitor_nvml())
    monitor.iniciar()
    try:
        transcritor = TranscritorWhisper(caminho(WHISPER_TURBO), monitor)
        for arquivo in arquivos:
            try:
                resultado = transcritor.transcrever(ler_wav(arquivo))
            except GpuOcupada as aviso:
                print(f"{arquivo.name}: {aviso}")
                continue
            except (OSError, ValueError) as erro:
                print(f"{arquivo.name}: {erro}")
                continue
            if arquivo.stem.endswith("_conversa"):
                # Na conversa o nome é dispensado, então não há o que conferir (D48).
                pedido = resultado.texto
            else:
                pedido = conferir_chamado(resultado.texto)
            if pedido is None:
                conferencia = "sem 'Ignis' no começo: seria descartado"
            elif not pedido:
                conferencia = "chamado sem pedido"
            else:
                conferencia = f"pedido: {pedido!r}"
            print(
                f"{arquivo.name}: {resultado.duracao_do_audio:.1f} s de áudio "
                f"em {1000 * resultado.segundos:.0f} ms\n"
                f"  texto: {resultado.texto!r}\n  {conferencia}"
            )
    finally:
        monitor.parar()
    return 0


def _gpu(limite: float) -> int:
    from ignis_cerebro.gpu import MonitorDeGpu, acompanhar_no_terminal, leitor_nvml

    monitor = MonitorDeGpu(leitor_nvml(), limite=limite)
    if not monitor.disponivel:
        return 1
    monitor.iniciar()
    print("Abra o jogo e veja a média. Ctrl+C para sair.")
    try:
        acompanhar_no_terminal(monitor)
    except KeyboardInterrupt:
        print("\nEncerrado.")
    finally:
        monitor.parar()
    return 0


if __name__ == "__main__":
    sys.exit(main())

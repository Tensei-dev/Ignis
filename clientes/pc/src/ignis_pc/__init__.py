"""Cliente de voz do Ignis para o PC."""

import argparse
import logging
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ignis-pc", description="Cliente de voz do Ignis para o PC."
    )
    comandos = parser.add_subparsers(dest="comando", required=True)
    comandos.add_parser(
        "baixar-modelos", help="Baixa e confere os modelos de voz usados pelo cliente."
    )
    escutar = comandos.add_parser(
        "escutar", help="Escuta o microfone e mostra os chamados e pedidos detectados."
    )
    escutar.add_argument(
        "--microfone", help='Parte do nome do microfone, como "High Definition".'
    )
    escutar.add_argument(
        "--depurar",
        action="store_true",
        help="Salva cada pedido como WAV em %%LOCALAPPDATA%%\\Ignis\\depuracao.",
    )
    argumentos = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if argumentos.comando == "baixar-modelos":
        return _baixar_modelos()
    if argumentos.comando == "escutar":
        from ignis_pc.terminal import escutar_no_terminal

        return escutar_no_terminal(argumentos.microfone, argumentos.depurar)
    return 0


def _baixar_modelos() -> int:
    from ignis_pc.modelos import TODOS, ErroDeModelo, baixar

    for modelo in TODOS:
        try:
            baixar(modelo)
        except (ErroDeModelo, OSError) as erro:
            logging.error("%s", erro)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

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
    argumentos = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if argumentos.comando == "baixar-modelos":
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

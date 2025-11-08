"""Application entry point."""

from __future__ import annotations

import sys

from PyQt6 import QtWidgets

from .binance_client import StreamSettings
from .config import load_config
from .widget import FloatingPriceWidget


def main() -> None:
    config = load_config()
    print("[Main] Inicializando QApplication...", flush=True)
    app = QtWidgets.QApplication(sys.argv)
    settings = StreamSettings(symbol=config.symbol)
    widget = FloatingPriceWidget(settings=settings)
    widget.show()
    print("[Main] Widget exibido, iniciando loop de eventos.", flush=True)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

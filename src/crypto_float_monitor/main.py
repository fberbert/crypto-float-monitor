"""Application entry point."""

from __future__ import annotations

import sys

from PyQt6 import QtWidgets

from .binance_client import StreamSettings
from .config import load_config
from .widget import FloatingPriceWidget

DEBUG = False


def main() -> None:
    config = load_config()
    if DEBUG:
        print("[Main] Inicializando QApplication...", flush=True)
    app = QtWidgets.QApplication(sys.argv)
    settings = StreamSettings(symbol=config.symbol)
    widget = FloatingPriceWidget(
        settings=settings,
        alert_above=config.alert_above,
        alert_below=config.alert_below,
    )
    widget.show()
    if DEBUG:
        print("[Main] Widget exibido, iniciando loop de eventos.", flush=True)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

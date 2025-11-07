"""Application entry point."""

from __future__ import annotations

import sys

from PyQt6 import QtWidgets

from .widget import FloatingPriceWidget


def main() -> None:
    print("[Main] Inicializando QApplication...", flush=True)
    app = QtWidgets.QApplication(sys.argv)
    widget = FloatingPriceWidget()
    widget.show()
    print("[Main] Widget exibido, iniciando loop de eventos.", flush=True)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

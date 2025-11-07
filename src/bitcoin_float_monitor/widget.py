"""Qt widget that displays the latest Bitcoin price."""

from __future__ import annotations

from typing import Optional

from PyQt6 import QtCore, QtGui, QtWidgets

from .binance_client import BinancePriceStreamer, StreamSettings


class FloatingPriceWidget(QtWidgets.QWidget):
    """A frameless, draggable widget that stays on top of the desktop."""

    def __init__(self, settings: StreamSettings | None = None, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._settings = settings or StreamSettings()
        self._drag_position: Optional[QtCore.QPoint] = None
        self._last_price: Optional[float] = None
        self._currency_prefix = self._currency_for_symbol(self._settings.symbol)

        self._price_label = QtWidgets.QLabel("Carregando…")
        self._price_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._price_label.setFont(QtGui.QFont("Sans Serif", 26, QtGui.QFont.Weight.Bold))
        self._price_label.setStyleSheet("color: #f5f5f5;")

        container = QtWidgets.QVBoxLayout()
        container.setContentsMargins(16, 16, 16, 16)
        container.setSpacing(6)
        container.addWidget(self._price_label)
        self.setLayout(container)

        self.setFixedWidth(300)
        self.setWindowTitle("Bitcoin Float Monitor")
        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint
            | QtCore.Qt.WindowType.WindowStaysOnTopHint
            | QtCore.Qt.WindowType.Window
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setStyleSheet(
            "background-color: rgba(20, 20, 20, 210);"
            "border-radius: 12px;"
            "padding: 8px;"
        )

        self._quit_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Q"), self)
        self._quit_shortcut.setContext(QtCore.Qt.ShortcutContext.ApplicationShortcut)
        self._quit_shortcut.activated.connect(self._handle_quit_shortcut)

        self._streamer = BinancePriceStreamer(settings=self._settings)
        self._streamer.price_updated.connect(self._handle_price_update)
        self._streamer.status_changed.connect(self._handle_status_update)
        self._streamer.start()
        self._log("Widget inicializado e stream iniciado.")
        self.adjustSize()
        QtCore.QTimer.singleShot(0, self._place_initially)

    # ------------------------------------------------------------------
    # Qt events
    # ------------------------------------------------------------------
    def mousePressEvent(self, a0: QtGui.QMouseEvent | None) -> None:  # noqa: N802 - Qt API
        event = a0
        if event and event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._drag_position = (event.globalPosition().toPoint() - self.frameGeometry().topLeft())
            event.accept()
            self._log(f"Início de arraste em {event.globalPosition().toPoint()}")
        super().mousePressEvent(event)

    def mouseMoveEvent(self, a0: QtGui.QMouseEvent | None) -> None:  # noqa: N802 - Qt API
        event = a0
        if event and event.buttons() & QtCore.Qt.MouseButton.LeftButton and self._drag_position is not None:
            new_pos = event.globalPosition().toPoint() - self._drag_position
            self.move(new_pos)
            event.accept()
            self._log(f"Arrastando widget para {new_pos}")
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, a0: QtGui.QMouseEvent | None) -> None:  # noqa: N802 - Qt API
        event = a0
        if event and event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._drag_position = None
            self._log("Arraste encerrado.")
        super().mouseReleaseEvent(event)

    def closeEvent(self, a0: QtGui.QCloseEvent | None) -> None:  # noqa: N802 - Qt API
        self._log("Fechando widget, encerrando streamer...")
        self._streamer.stop()
        super().closeEvent(a0)

    # ------------------------------------------------------------------
    # Stream callbacks
    # ------------------------------------------------------------------
    @QtCore.pyqtSlot(float)
    def _handle_price_update(self, price: float) -> None:
        # color = "#f5f5f5"
        color = "#38b000"  # default to green for first update
        if self._last_price is not None:
            if price > self._last_price:
                color = "#38b000"
            elif price < self._last_price:
                color = "#ff4d4f"
        self._price_label.setStyleSheet(f"color: {color};")
        self._price_label.setText(self._format_price(price))
        self._last_price = price
        self._log(f"Atualização de preço recebida: {price}")

    @QtCore.pyqtSlot(str)
    def _handle_status_update(self, status: str) -> None:
        self._log(f"Status de conexão atualizado: {status}")

    def _handle_quit_shortcut(self) -> None:
        self._log("Atalho 'q' detectado. Encerrando aplicação.")
        app = QtWidgets.QApplication.instance()
        if app is not None:
            app.quit()
        else:
            QtCore.QCoreApplication.quit()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _format_price(self, price: float) -> str:
        formatted = f"{price:,.2f}"
        if self._currency_prefix == "R$":
            formatted = formatted.replace(",", "v").replace(".", ",").replace("v", ".")
        prefix = f"{self._currency_prefix} " if self._currency_prefix else ""
        return f"{prefix}{formatted}".strip()

    def _place_initially(self) -> None:
        screen = QtGui.QGuiApplication.primaryScreen()
        if not screen:
            self._log("Nenhuma tela detectada para posicionamento inicial.")
            return
        available = screen.availableGeometry()
        x = available.right() - self.width() - 20
        y = available.top() + 20
        target = QtCore.QPoint(max(available.left(), x), max(available.top(), y))
        self.move(target)
        self._log(f"Widget posicionado inicialmente em {target}")

    @staticmethod
    def _log(message: str) -> None:
        print(f"[FloatingPriceWidget] {message}", flush=True)

    @staticmethod
    def _currency_for_symbol(symbol: str) -> str:
        upper = symbol.upper()
        if upper.endswith("USDT") or upper.endswith("USD"):
            return "$"
        if upper.endswith("BRL"):
            return "R$"
        if upper.endswith("EUR"):
            return "€"
        return ""


"""Qt widget that displays the latest Bitcoin price."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer

from .binance_client import BinancePriceStreamer, StreamSettings
from .config import save_alerts


class FloatingPriceWidget(QtWidgets.QWidget):
    """A frameless, draggable widget that stays on top of the desktop."""

    def __init__(
        self,
        settings: StreamSettings | None = None,
        parent: Optional[QtWidgets.QWidget] = None,
        *,
        alert_above: float | None = None,
        alert_below: float | None = None,
    ) -> None:
        super().__init__(parent)
        self._settings = settings or StreamSettings()
        self._drag_position: Optional[QtCore.QPoint] = None
        self._last_price: Optional[float] = None
        self._currency_prefix = self._currency_for_symbol(self._settings.symbol)
        self._alert_cooldown = 60.0  # seconds
        self._alert_above: float | None = None
        self._alert_below: float | None = None
        self._last_alert_ts: dict[str, float] = {"above": 0.0, "below": 0.0}
        self._alert_ready: dict[str, bool] = {"above": False, "below": False}
        self._audio_manager = _AlertAudioManager(self)
        self._alert_sounds = {
            "above": self._resolve_sound_path("alert_above.mp3"),
            "below": self._resolve_sound_path("alert_below.mp3"),
        }
        self._set_alert_thresholds(alert_above, alert_below)

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
        self.setWindowTitle("Crypto Float Monitor")
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

    def mouseDoubleClickEvent(self, a0: QtGui.QMouseEvent | None) -> None:  # noqa: N802 - Qt API
        event = a0
        if event and event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._open_alert_dialog()
            event.accept()
        super().mouseDoubleClickEvent(event)

    def closeEvent(self, a0: QtGui.QCloseEvent | None) -> None:  # noqa: N802 - Qt API
        self._log("Fechando widget, encerrando streamer...")
        self._streamer.stop()
        super().closeEvent(a0)

    # ------------------------------------------------------------------
    # Stream callbacks
    # ------------------------------------------------------------------
    @QtCore.pyqtSlot(float)
    def _handle_price_update(self, price: float) -> None:
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
        self._maybe_trigger_alert(price)

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
    def _maybe_trigger_alert(self, price: float) -> None:
        now = time.monotonic()
        if self._alert_above is not None:
            if price >= self._alert_above:
                if (
                    self._alert_ready["above"]
                    and now - self._last_alert_ts["above"] >= self._alert_cooldown
                ):
                    self._play_alert("above")
                    self._last_alert_ts["above"] = now
                    self._alert_ready["above"] = False
            elif price < self._alert_above:
                self._alert_ready["above"] = True

        if self._alert_below is not None:
            if price <= self._alert_below:
                if (
                    self._alert_ready["below"]
                    and now - self._last_alert_ts["below"] >= self._alert_cooldown
                ):
                    self._play_alert("below")
                    self._last_alert_ts["below"] = now
                    self._alert_ready["below"] = False
            elif price > self._alert_below:
                self._alert_ready["below"] = True

    def _open_alert_dialog(self) -> None:
        dialog = AlertThresholdDialog(self._alert_above, self._alert_below, self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            above, below = dialog.values
            self._set_alert_thresholds(above, below)
            save_alerts(above, below)
            self._log(
                f"Alertas atualizados: acima={above if above is not None else 'desativado'}, "
                f"abaixo={below if below is not None else 'desativado'}"
            )

    def _set_alert_thresholds(self, alert_above: float | None, alert_below: float | None) -> None:
        self._alert_above = alert_above
        self._alert_below = alert_below
        self._last_alert_ts = {"above": 0.0, "below": 0.0}
        self._alert_ready = {
            "above": alert_above is not None,
            "below": alert_below is not None,
        }

    def _play_alert(self, key: str) -> None:
        path = self._alert_sounds.get(key)
        if not path:
            self._log(f"Arquivo de áudio para alerta '{key}' não encontrado.")
            return
        self._audio_manager.play(key, path)

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

    def _resolve_sound_path(self, filename: str) -> Path | None:
        package_path = Path(__file__).resolve().parent / "assets" / filename
        if package_path.exists():
            return package_path
        repo_path = Path(__file__).resolve().parents[2] / "assets" / filename
        if repo_path.exists():
            return repo_path
        return None

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


class _AlertAudioManager(QtCore.QObject):
    """Simple helper around QMediaPlayer to play short alert sounds."""

    def __init__(self, parent: Optional[QtCore.QObject] = None) -> None:
        super().__init__(parent)
        self._players: dict[str, QMediaPlayer] = {}
        self._audio_outputs: dict[str, QAudioOutput] = {}

    def play(self, key: str, path: Path) -> None:
        player = self._players.get(key)
        audio_output = self._audio_outputs.get(key)

        if player is None or audio_output is None:
            audio_output = QAudioOutput()
            player = QMediaPlayer()
            player.setAudioOutput(audio_output)
            self._players[key] = player
            self._audio_outputs[key] = audio_output

        if player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            player.stop()

        audio_output.setVolume(1.0)
        player.setSource(QtCore.QUrl.fromLocalFile(str(path)))
        player.play()


class AlertThresholdDialog(QtWidgets.QDialog):
    """Modal dialog for editing alert thresholds."""

    def __init__(
        self,
        alert_above: float | None,
        alert_below: float | None,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Alert thresholds")
        self.setModal(True)
        self._result: tuple[float | None, float | None] = (alert_above, alert_below)

        layout = QtWidgets.QFormLayout()

        self._above_input = QtWidgets.QLineEdit(self._format_value(alert_above))
        self._above_input.setPlaceholderText("Ex.: 102500")
        layout.addRow("Alert above", self._above_input)

        self._below_input = QtWidgets.QLineEdit(self._format_value(alert_below))
        self._below_input.setPlaceholderText("Ex.: 98000")
        layout.addRow("Alert below", self._below_input)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Save
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        wrapper = QtWidgets.QVBoxLayout(self)
        wrapper.addLayout(layout)
        wrapper.addWidget(buttons)
        self._apply_scaling()

    @property
    def values(self) -> tuple[float | None, float | None]:
        return self._result

    def accept(self) -> None:  # type: ignore[override]
        try:
            above = self._parse(self._above_input.text())
            below = self._parse(self._below_input.text())
        except ValueError as exc:
            QtWidgets.QMessageBox.warning(self, "Invalid value", str(exc))
            return
        self._result = (above, below)
        super().accept()

    @staticmethod
    def _parse(text: str) -> float | None:
        stripped = text.strip()
        if not stripped:
            return None
        try:
            return float(stripped)
        except ValueError as exc:  # pragma: no cover
            raise ValueError("Use números válidos ou deixe em branco para desativar.") from exc

    @staticmethod
    def _format_value(value: float | None) -> str:
        return "" if value is None else f"{value:.2f}"

    def _apply_scaling(self) -> None:
        font = self.font()
        font.setPointSizeF(font.pointSizeF() * 2)
        self.setFont(font)
        layout = self.layout()
        if layout is not None:
            layout.activate()
        base_size = self.sizeHint()
        # self.resize(int(base_size.width() * 2), int(base_size.height() * 2))

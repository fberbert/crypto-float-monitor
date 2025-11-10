"""Binance WebSocket streaming utilities."""

from __future__ import annotations

import json
import ssl
import threading
import time
from dataclasses import dataclass

from PyQt6 import QtCore
import websocket

DEBUG = False

DEBUG = False


@dataclass(frozen=True)
class StreamSettings:
    symbol: str = "BTCUSDT"
    base_url: str = "wss://stream.binance.com:9443/ws"
    reconnect_delay: float = 3.0

    @property
    def stream_url(self) -> str:
        return f"{self.base_url}/{self.symbol.lower()}@trade"


class BinancePriceStreamer(QtCore.QObject):
    """Connects to Binance and emits trade prices via Qt signals."""

    price_updated = QtCore.pyqtSignal(float)
    status_changed = QtCore.pyqtSignal(str)

    def __init__(self, settings: StreamSettings | None = None, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)
        self._settings = settings or StreamSettings()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._ws_app: websocket.WebSocketApp | None = None
        self._log(f"Inicializando streamer para {self._settings.symbol}")

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._log("Iniciando thread de stream...")
        self._thread = threading.Thread(target=self._run, name="BinancePriceStreamer", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._log("Solicitando parada do streamer...")
        if self._ws_app:
            try:
                self._ws_app.close()
            except Exception:
                pass
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        self._log("Streamer parado.")

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------
    def _run(self) -> None:
        while not self._stop_event.is_set():
            self.status_changed.emit("Connecting…")
            self._log(f"Conectando em {self._settings.stream_url}")
            self._ws_app = websocket.WebSocketApp(
                self._settings.stream_url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
            )
            try:
                self._ws_app.run_forever(
                    sslopt={"cert_reqs": ssl.CERT_REQUIRED},
                    ping_interval=20,
                    ping_timeout=10,
                )
            except Exception as exc:  # pragma: no cover - defensive
                self.status_changed.emit(f"Erro: {exc}")
                self._log(f"Erro no stream: {exc}")
            finally:
                self._ws_app = None

            if self._stop_event.is_set():
                break

            self.status_changed.emit("Reconectando…")
            self._log(f"Aguardando {self._settings.reconnect_delay}s para reconectar...")
            time.sleep(self._settings.reconnect_delay)

    def _on_open(self, *_: object) -> None:
        self.status_changed.emit("Conectado")
        self._log("WebSocket aberto.")

    def _on_close(self, *_: object) -> None:
        self.status_changed.emit("Desconectado")
        self._log("WebSocket fechado.")

    def _on_error(self, _ws: websocket.WebSocketApp, error: Exception) -> None:
        self.status_changed.emit(f"Erro: {error}")
        self._log(f"Erro recebido: {error}")

    def _on_message(self, _ws: websocket.WebSocketApp, message: str) -> None:
        try:
            payload = json.loads(message)
            price = float(payload["p"])
        except (ValueError, KeyError, TypeError):
            return
        self.price_updated.emit(price)
        self._log(f"Preço recebido: {price}")

    def _log(self, message: str) -> None:
        if not DEBUG:
            return
        print(f"[BinancePriceStreamer] {message}", flush=True)

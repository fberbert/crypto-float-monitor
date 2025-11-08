# bitcoin-float-monitor

Floating PyQt6 widget that keeps the Bitcoin price (pair `BTCUSDT`) in real time using Binance's official stream. The value stays on top of the desktop, changes color according to price movement (green for up, red for down), and you can exit quickly with the `q` key.

<p align="center">
  <img src="https://github.com/fberbert/bitcoin-float-monitor/raw/main/assets/bitcoin-float-monitor.gif" alt="Bitcoin Float Monitor demo" />
</p>

## Requirements

- Python 3.10+
- Linux with a graphical session (X11/Wayland) and PyQt6 support

## Running

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
bitcoin-float-monitor
```

The widget opens as a small floating window and remains visible at all times:

- Click and drag to reposition.
- Press `q` at any time to quit the app.
- The price color indicates the latest move (green = up, red = down).

## Configuration

On first launch the app creates a config file at `${XDG_CONFIG_HOME:-$HOME/.config}/bitcoin-float-monitor/config.json`. The default content is:

```json
{
  "symbol": "BTCUSDT"
}
```

Edit the `symbol` value to monitor another Binance pair (e.g., `ETHUSDT`). The app reads this file every time it starts.

### AppImage build

The repository ships with an AppImage recipe under `AppDir/`. To build and run locally:

```bash
appimagetool AppDir
chmod +x Bitcoin_Float_Monitor-x86_64.AppImage
./Bitcoin_Float_Monitor-x86_64.AppImage
```

For end users, distribute the generated `.AppImage` binary—after downloading they only need to `chmod +x` and execute it.

## Project structure

- `pyproject.toml` – app metadata and dependencies.
- `src/bitcoin_float_monitor/binance_client.py` – WebSocket client that consumes the `BTCUSDT@trade` stream.
- `src/bitcoin_float_monitor/widget.py` – Qt widget responsible for the floating UI.
- `src/bitcoin_float_monitor/main.py` – entry point (`bitcoin-float-monitor`).

## Author

- Fábio Berbert de Paula
- fberbert@gmail.com
- https://github.com/fberbert/

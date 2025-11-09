# crypto-float-monitor

Floating PyQt6 widget that keeps the Bitcoin price (pair `BTCUSDT`) in real time using Binance's official stream. The value stays on top of the desktop, changes color according to price movement (green for up, red for down), and you can exit quickly with the `q` key.

<p align="center">
  <img src="https://github.com/fberbert/crypto-float-monitor/raw/main/assets/crypto-float-monitor.gif" alt="Crypto Float Monitor demo" />
</p>

## Requirements

- Python 3.10+
- Linux with a graphical session (X11/Wayland) and PyQt6 support

## Running

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
crypto-float-monitor
```

The widget opens as a small floating window and remains visible at all times:

- Click and drag to reposition.
- Press `q` at any time to quit the app.
- Double-click the widget to edit alert thresholds without touching the config file.
- The price color indicates the latest move (green = up, red = down).

## Configuration

On first launch the app creates a config file at `${XDG_CONFIG_HOME:-$HOME/.config}/crypto-float-monitor/config.json`. The default content is:

```json
{
  "symbol": "BTCUSDT",
  "alert_above": null,
  "alert_below": null
}
```

Edit the `symbol` value to monitor another Binance pair (e.g., `ETHUSDT`). Set `alert_above` or `alert_below` to a numeric price (or keep `null` to disable) to receive audio notices whenever the price crosses those thresholds. Alerts reuse local MP3 files in `assets/alert_above.mp3` and `assets/alert_below.mp3`, enforce a 60-second cooldown, and can be updated in-app by double-clicking the widget (the modal writes your changes back to `config.json`). The app reads this file every time it starts.

### AppImage build

The repository ships with an AppImage recipe under `scripts/build_appimage.sh`. To build and run locally:

```bash
scripts/build_appimage.sh
./appimagetool build/AppDir Crypto_Float_Monitor-x86_64.AppImage
chmod +x Crypto_Float_Monitor-x86_64.AppImage
./Crypto_Float_Monitor-x86_64.AppImage
```

For end users, distribute the generated `.AppImage` binary—after downloading they only need to `chmod +x` and execute it.
The build process copies the bundled MP3 alert sounds into the AppImage, so the package is self-contained even on systems sem áudio pré-instalado.


#### GitHub Actions release

CI/CD is available via the *Release AppImage* workflow (Actions tab). Run the workflow manually, provide a tag such as `v0.1.1`, and it will:

1. Build the AppImage using `scripts/build_appimage.sh`.
2. Run basic checks.
3. Create the git tag and publish a GitHub Release with the generated AppImage attached.


## Project structure

- `pyproject.toml` – app metadata and dependencies.
- `src/crypto_float_monitor/binance_client.py` – WebSocket client that consumes the `BTCUSDT@trade` stream.
- `src/crypto_float_monitor/widget.py` – Qt widget responsible for the floating UI.
- `src/crypto_float_monitor/main.py` – entry point (`crypto-float-monitor`).

## Author

- Fábio Berbert de Paula
- fberbert@gmail.com
- https://github.com/fberbert/

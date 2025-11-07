# bitcoin-float-monitor

Widget flutuante em PyQt6 que mantém a cotação do Bitcoin (par `BTCUSDT`) em tempo real usando o stream oficial da Binance. O valor fica sempre visível sobre o desktop, troca de cor conforme o movimento (verde para alta, vermelho para queda) e pode ser encerrado rapidamente com a tecla `q`.

## Pré-requisitos

- Python 3.10+
- Sistema Linux com servidor gráfico (X11/Wayland) e suporte ao PyQt6

## Como executar

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
bitcoin-float-monitor
```

O widget abrirá como uma pequena janela flutuante e ficará sempre visível no desktop:

- Clique e arraste para reposicionar.
- Pressione `q` a qualquer momento para fechar a aplicação.
- A cor do valor indica a direção da última variação (verde = alta, vermelho = queda).

## Estrutura do projeto

- `pyproject.toml` – metadata e dependências do app.
- `src/bitcoin_float_monitor/binance_client.py` – cliente WebSocket que consome o stream `BTCUSDT@trade`.
- `src/bitcoin_float_monitor/widget.py` – widget Qt responsável pela interface flutuante.
- `src/bitcoin_float_monitor/main.py` – ponto de entrada (`bitcoin-float-monitor`).

## Próximos passos sugeridos

- Adicionar testes automatizados para o formatter de preço.
- Permitir configuração do par/símbolo via linha de comando.
- Disponibilizar binários empacotados (AppImage, Flatpak, etc.) para facilitar a instalação.

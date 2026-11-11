# WealthRank

Interactive stock and Indian mutual-fund portfolio analytics, explainable recommendations, performance charts, and an inflation-aware FIRE calculator.

Built with **Python, Streamlit, Plotly, yfinance and MFapi.in**. No API keys needed.

## Run locally

Use Python 3.10+.

### Windows (PowerShell)

```powershell
git clone https://github.com/RohitSuhasReddy/WealthRank.git
cd WealthRank
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

### macOS / Linux

```bash
git clone https://github.com/RohitSuhasReddy/WealthRank.git
cd WealthRank
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Open **http://localhost:8501**.

Use the editable example holdings or upload a CSV / XLSX with `Ticker`, `Quantity`, optional `Avg Buy Price`, and optional `Type` (`Stock` or `Mutual fund`). Use Yahoo Finance tickers for stocks and AMFI scheme codes for mutual funds. Click **Analyse my portfolio**, then **Discover matches**.

## Tests

```bash
python -m pip install -r requirements-dev.txt
pytest -q
```

Prices / NAVs are fetched on demand and may be delayed or unavailable. FIRE projections are hypothetical. Recommendations are rule-based educational matches, not investment advice. The model lab uses **synthetic** profiles and clicks, not real A/B-test results.

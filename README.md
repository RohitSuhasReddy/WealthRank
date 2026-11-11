# WealthRank

An interactive personal-finance application with an animated **solar-system navigation**. The five standalone screens are **Portfolio**, **Stock Analytics**, **Discover**, **FIRE Planner**, and **Model Lab**.

Built with Python, Streamlit, Plotly, yfinance and MFapi.in. No paid API keys.

## Run

Python 3.10+.

**Windows PowerShell**

```powershell
git clone https://github.com/RohitSuhasReddy/WealthRank.git
cd WealthRank
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

**macOS / Linux**

```bash
git clone https://github.com/RohitSuhasReddy/WealthRank.git
cd WealthRank
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Open **http://localhost:8501**. Click a planet to open a screen. Import the sample holdings or upload a CSV/XLSX with `Ticker`, `Quantity`, optional `Avg Buy Price` and `Type` (Stock / Mutual fund). Yahoo Finance tickers and AMFI scheme codes are supported. Click **Analyse my portfolio** to fetch quotes, then **Discover** to rank up to ten eligible stocks.

Net-worth and FIRE monetary text fields accept Indian commas, e.g. `25,00,000`.

## Tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Market data may be unavailable or delayed. Rankings are transparent heuristic matches, **not** investment advice. Alpha/beta and other historical metrics are descriptive, not predictive. FIRE is a modelled scenario; Model Lab experiments use **synthetic** data.

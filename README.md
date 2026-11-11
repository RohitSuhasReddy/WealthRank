# WealthRank

**Know your portfolio. Understand your risk. Plan your financial future.**

WealthRank is a Python + Streamlit personal-finance dashboard for Indian and US stocks and Indian mutual funds. Its animated solar-system homepage opens five independent workspaces.

## What it does

- **Portfolio & Net Worth:** Import CSV/Excel holdings, edit quantities and purchase dates, view valuations and asset allocation, and calculate net worth from assets and liabilities or a single entered total.
- **Stock Analytics:** Inspect each holding's historical returns, alpha, beta, volatility, Sharpe ratio, drawdown, and interactive price or percentage-change charts.
- **Discover:** Choose **India / US → sector** for up to **10 ranked stocks per category**. See risk flags and performance metrics; stocks you already hold are highlighted separately.
- **FIRE Planner:** Estimate inflation-adjusted retirement expenses and required corpus, project net worth, and compare SIP and spending scenarios. Enter exact values or use sliders.
- **Model Lab:** Explore offline ranking metrics, feature ablations, and a **synthetic** A/B simulation (not real user experiment results).

Market prices are fetched from **Yahoo Finance** (`yfinance`) and Indian mutual-fund NAVs from **MFapi.in / AMFI**. Interactive charts use **Plotly**. No paid API keys are required.

## First-time setup

Requires **Python 3.10+** and **Git**.

**Windows (PowerShell)**

```powershell
git clone https://github.com/RohitSuhasReddy/WealthRank.git
cd WealthRank
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

**macOS / Linux**

```bash
git clone https://github.com/RohitSuhasReddy/WealthRank.git
cd WealthRank
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open **http://localhost:8501**. Stop the server with **Ctrl+C**.

## Later launches

Open a terminal in your existing `WealthRank` folder; **do not clone or recreate the environment again**.

**Windows (PowerShell)**

```powershell
.\.venv\Scripts\Activate.ps1
python -m streamlit run app.py
```

**macOS / Linux**

```bash
source .venv/bin/activate
python -m streamlit run app.py
```

To get new changes, run `git pull origin main` from the project folder before launching. If dependencies changed, run `python -m pip install -r requirements.txt` again.

## Add a portfolio

Open **Portfolio**, upload a `.csv` or `.xlsx`, or add rows manually. Required columns: `Ticker`, `Quantity`. Optional: `Type` (`Stock` / `Mutual fund`), `Avg Buy Price`, `Purchase Date` (`YYYY-MM-DD`). Use Yahoo Finance tickers (e.g. `INFY.NS`, `AAPL`) or AMFI scheme codes for funds. A small example CSV is available at [`examples/portfolio.csv`](examples/portfolio.csv).

Click **Analyse my portfolio** to fetch prices and open Analytics. Uploaded and edited holdings are retained **while the current Streamlit session is active**, not permanently stored across server restarts.

## Testing

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

> **Note:** Quotes and NAVs can be delayed or unavailable. Ranking scores are explainable screening heuristics, not buy recommendations or return forecasts. Historical metrics do not predict future results. FIRE values are hypothetical and do not guarantee retirement outcomes.

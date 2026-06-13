# Narrow CPR Scanner

A Python-based scanner that identifies stocks/instruments with **Narrow CPR (Central Pivot Range)** — a key concept in options and intraday trading strategy.

## Files
- `app.py` — Main application entry point
- `scanner.py` — Core CPR scanning logic
- `location.py` — Location/instrument utilities
- `download_instruments.py` — Downloads instrument data
- `test_ohlc.py` — OHLC data testing
- `data/` — Instrument and CPR state data
- `logs/` — Application logs

## Setup
1. Install dependencies
2. Add your broker API credentials to `key.txt` (⚠️ never commit this file)
3. Run `python app.py`

## ⚠️ Security Note
`key.txt` contains API credentials and is excluded via `.gitignore`. Never commit secrets to version control.

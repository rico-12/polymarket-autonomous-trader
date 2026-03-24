# 🤖 Polymarket Autonomous Trader v2.0

**Status**: Production Ready (dengan retry + circuit breaker)

## Overview

Full autonomous trading agent untuk Polymarket prediction markets. Sistem ini scan market, hitung probability, cari edge, dan execute bet otomatis dengan risk management ketat.

## Perubahan Terbaru (25 Mar 2026)

- ✅ Pakai `python-dotenv` (lebih aman & clean)
- ✅ Semua `ast.literal_eval` diganti `json.loads`
- ✅ Global client singleton + retry 3x
- ✅ Rich logging
- ✅ Circuit breaker otomatis
- ✅ Hard limit: max $1 per bet, max 3 bet/hari

## Cara Install

```bash
git clone https://github.com/rico-12/polymarket-autonomous-trader.git
cd polymarket-autonomous-trader
pip install -r requirements.txt
cp .env.example .env
# Edit .env dengan POLYCLAW_PRIVATE_KEY (wallet kecil!)
```

## Cara Jalankan

```bash
# Full autonomous (auto bet)
python scripts/autonomous_runner.py

# Atau test balance dulu
python scripts/trader.py
```

## Files

- `scripts/autonomous_runner.py` → Main bot (autonomous)
- `scripts/trader.py` → Trading core (py-clob-client)
- `scripts/analyst.py` → Analysis tools
- `polymarket-scanner.py` → Scanner for market monitoring
- `trades_log.md` → Auto-generated trade history
- `requirements.txt` → Dependencies
- `.env.example` → Template environment

## Risk Rules

| Rule | Value |
|------|-------|
| Max bet size | $1.00 |
| Max bets/day | 3 |
| Min balance | $5.00 |
| Edge threshold | ≥ 8% |
| Confidence | HIGH/MEDIUM only |

## Security

- Private key di `.env` saja (di-gitignore)
- Pakai wallet kecil untuk trading
- Jangan pernah share credentials

## Channel

Telegram notifications dikirim ke:
- Channel: `@RimuruPolymarket`

## Target

Winrate 60%+ dengan disiplin ketat.

---

**⚠️ Disclaimer**: Trading prediction markets involves risk. Use only small wallet. All automated.
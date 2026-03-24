# 🚀 Polymarket Autonomous Trader

**Full autonomous trading agent** untuk Polymarket. Scan → Research → Edge calculation → Bet sendiri dengan **max $1 per bet**.

## Fitur Utama

- Real-time scanner Gamma API
- Chain-of-Thought probability estimation
- Edge ≥ 8% + confidence filter
- **Hard risk rules** (max $1, max 5 posisi, max 3 bet/hari)
- Telegram notification
- Rich logging + auto log ke `trades_log.md`
- Circuit breaker & retry mechanism

## Quick Start

```bash
# 1. Clone repo
git clone https://github.com/rico-12/polymarket-autonomous-trader.git
cd polymarket-autonomous-trader

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup environment
cp .env.example .env
# Edit .env dengan API keys lo (PAKE WALLET KECIL!)

# 4. Run autonomous trader
python scripts/autonomous_runner.py
```

## File Penting

| File | Description |
|------|-------------|
| `scripts/autonomous_runner.py` | Main bot - full autonomous |
| `scripts/trader.py` | Trading core (py-clob-client) |
| `trades_log.md` | History auto-generated |
| `SKILL.md` | Dokumentasi lengkap untuk OpenClaw |

## Security

⚠️ **PENTING:**
- Pakai wallet kecil专门 untuk trading
- Private key hanya di `.env` (sudah di-gitignore)
- Jangan pernah share private key

## Target

Winrate 60%+ dengan disiplin ketat + risk management.

## License

MIT
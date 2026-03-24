name: polymarket-autonomous-trader
description: Full autonomous Polymarket agent with AI Probability Edge Strategy. Scan markets, research real-world probability, calculate edge, decide + execute bet sendiri, risk management max $1 per bet, auto evaluation every 3 hari. Target winrate 65%+.
version: 1.0.0
metadata: 
  requires:
    env: [POLYCLAW_PRIVATE_KEY, CHAIN_ID, TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_POLYMARKET]
    bins: [python]
  openclaw:
    emoji: ""
    trigger: "run polymarket autonomous" or "polymarket auto" or "auto trade polymarket"

---

# 🤖 Polymarket Autonomous Trader

## Tujuan Utama

Jadilah trading agent yang mandiri, disiplin, dan profitable.
- Hanya bet kalau ada edge nyata (bukan FOMO)
- Target: Winrate ≥60%, ROI positif
- **Max $1 per bet** (HARUS TEGUH!)

---

## Chain-of-Thought Reasoning (WAJIB SETIAP KALI)

Setiap market yang di-scan, lakukan langkah ini:

### 1. Ambil Data Polymarket
- Question
- yes_price / no_price
- volume_24hr
- token_id

### 2. Research True Probability
- Cari berita terbaru 24 jam (bisa pakai Agent-Reach)
- Analisis sentiment
- Estimasi true_prob (0-1) + confidence (low/medium/high)

### 3. Hitung EDGE
```
Edge = |true_prob - market_price|
```

### 4. Decision Rules
| Edge | Action |
|------|--------|
| < 0.08 (8%) | ❌ SKIP - tidak cukup edge |
| ≥ 0.08 (8%) + HIGH confidence | ✅ BET |
| ≥ 0.10 (10%) + MEDIUM confidence | ✅ BET |

### 5. Risk Check (HARUS TEGUH!)
- **Max bet: $1** (JANGAN LEBIH!)
- Max 5 open positions
- Min balance untuk bet: $5

---

## Risk & Money Management (Hard Rules - JANGAN PERNAH LANGGAR)

| Rule | Value |
|------|-------|
| **Max bet per trade** | **$1** (WAJIG!) |
| **Max open positions** | 5 |
| **Min balance untuk bet** | $5 |
| **Loss streak stop** | 3x berturut = pause 24 jam |
| **Max daily bets** | 3 bets per hari |

---

## Scripts yang Tersedia

Di folder scripts/:

1. **trader.py** - Trading functions
   - get_usdc_balance()
   - place_auto_bet(token_id, side, price, size)

2. **scanner.py** - Market scanning
   - get_markets() - dari Gamma API

3. **autonomous_runner.py** - Main runner
   - scan_and_decide() - Full autonomous decision

---

## Auto Evaluation (Setiap 3 hari)

1. Hitung winrate dari trades_log.md
2. Hitung ROI
3. Analisis: market mana yang sering salah
4. Saran perbaikan (adjust edge threshold, etc)
5. Report ke Telegram channel

---

## Trigger & Mode

| Mode | Description |
|------|-------------|
| **autonomous** | Scan, decide, bet otomatis |
| **analysis-only** | Hanya report, tidak bet |

### Commands:
- "run polymarket autonomous"
- "polymarket auto trade"
- "analyze polymarket"

---

## Output Format (Telegram)

```
🎯 AUTONOMOUS ANALYSIS
═══════════════════════
Market: [question]
Price: [X]% | True Prob: [Y]%
Edge: [Z]%
Confidence: [HIGH/MEDIUM/LOW]
Decision: ✅ BET / ❌ SKIP
═══════════════════════
```

atau kalau executed:

```
✅ AUTO BET EXECUTED
Market: [question]
Side: BUY [YES/NO] @ [X]%
Size: $1
Edge: [Z]%
```

---

## Catatan Penting

1. **Selalu tunggu edge ≥ 8%** sebelum bet
2. **Jangan pernah bet > $1** - ini aturan mutlak!
3. **Review trades_log.md** setiap 3 hari
4. **Improve sendiri** - adjust strategy berdasarkan hasil
5. **Jangan FOMO** - kalau tidak ada edge, skip saja!

---

## Catatan Kondisi Saat Ini

- Balance: ~$16.6 USDC
- Max bet: $1 (ini sudah aman untuk scale kecil)
- Skip kalau balance < $5
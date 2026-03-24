"""
Signal & Position Logging System
Records every signal with reasoning for future evaluation
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path

# Base directory
SCRIPT_DIR = Path(__file__).parent
LOG_FILE = SCRIPT_DIR / "signal_history.json"
EVAL_FILE = SCRIPT_DIR / "evaluations.json"

def load_log():
    """Load existing signal log"""
    if LOG_FILE.exists():
        with open(LOG_FILE, 'r') as f:
            return json.load(f)
    return {"signals": [], "positions": []}

def save_log(data):
    """Save signal log"""
    with open(LOG_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def log_signal(signal_data):
    """
    Log a trading signal with full reasoning
    
    signal_data = {
        "symbol": "FILUSDT",
        "direction": "LONG",
        "score": 65,
        "indicators": {...},
        "reasoning": "RSI oversold, MACD bullish crossover, volume spike...",
        "timestamp": "2026-03-23T03:36:00",
        "price": 0.919,
        "action": "OPEN" or "SKIP"
    }
    """
    data = load_log()
    
    log_entry = {
        **signal_data,
        "logged_at": datetime.now().isoformat()
    }
    
    data["signals"].append(log_entry)
    save_log(data)
    
    return log_entry

def log_position(position_data):
    """
    Log position with entry details
    
    position_data = {
        "symbol": "FILUSDT",
        "direction": "LONG",
        "entry_price": 0.919,
        "quantity": 265,
        "leverage": 10,
        "tp_price": 1.29,
        "sl_price": 0.74,
        "signal_score": 65,
        "signal_reasoning": "...",
        "opened_at": "2026-03-23T03:36:00"
    }
    """
    data = load_log()
    
    entry = {
        **position_data,
        "logged_at": datetime.now().isoformat(),
        "status": "OPEN",
        "closed_at": None,
        "pnl": None,
        "result": None  # "TP" / "SL" / "MANUAL"
    }
    
    data["positions"].append(entry)
    save_log(data)
    
    return entry

def update_position(symbol, updates):
    """Update position status (for TP/SL/close)"""
    data = load_log()
    
    for pos in data["positions"]:
        if pos["symbol"] == symbol and pos.get("status") == "OPEN":
            pos.update(updates)
            pos["updated_at"] = datetime.now().isoformat()
    
    save_log(data)

def get_signals(days=7):
    """Get signals from last N days"""
    data = load_log()
    cutoff = datetime.now() - timedelta(days=days)
    
    return [s for s in data["signals"] 
            if datetime.fromisoformat(s["logged_at"]) > cutoff]

def get_positions(days=30):
    """Get positions from last N days"""
    data = load_log()
    cutoff = datetime.now() - timedelta(days=days)
    
    return [p for p in data["positions"] 
            if datetime.fromisoformat(p.get("logged_at", "2020")) > cutoff]

def evaluate_performance():
    """
    Evaluate trading performance for improvement
    
    Returns:
        - Total positions
        - Win rate
        - Average PnL
        - Best/worst signals
        - Recommendations
    """
    positions = get_positions(30)
    signals = get_signals(7)
    
    # Calculate stats
    closed = [p for p in positions if p.get("status") != "OPEN"]
    open_pos = [p for p in positions if p.get("status") == "OPEN"]
    
    wins = sum(1 for p in closed if p.get("result") == "TP")
    losses = sum(1 for p in closed if p.get("result") == "SL")
    total_closed = wins + losses
    
    win_rate = (wins / total_closed * 100) if total_closed > 0 else 0
    
    # Analyze by indicators
    indicator_performance = {}
    for pos in closed:
        reason = pos.get("signal_reasoning", "unknown")
        key = reason[:50] if reason else "unknown"
        if key not in indicator_performance:
            indicator_performance[key] = {"total": 0, "wins": 0}
        indicator_performance[key]["total"] += 1
        if pos.get("result") == "TP":
            indicator_performance[key]["wins"] += 1
    
    return {
        "total_positions": len(positions),
        "closed_positions": total_closed,
        "open_positions": len(open_pos),
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 2),
        "indicator_performance": indicator_performance,
        "recent_signals": signals[-10:] if signals else [],
        "recommendations": generate_recommendations(win_rate, indicator_performance)
    }

def generate_recommendations(win_rate, indicator_performance):
    """Generate improvement recommendations"""
    recs = []
    
    if win_rate < 40:
        recs.append("⚠️ Win rate rendah - pertimbangkan score threshold lebih tinggi")
        recs.append("   Saat ini: ≥50, pertimbangkan ≥60")
    
    if win_rate > 60:
        recs.append("✅ Win rate bagus - bisa pertimbangkan lebih agresif")
    
    # Find best indicators
    best_indicators = []
    worst_indicators = []
    
    for ind, stats in indicator_performance.items():
        if stats["total"] >= 2:
            rate = stats["wins"] / stats["total"] * 100
            if rate > 70:
                best_indicators.append((ind, rate, stats["total"]))
            elif rate < 40:
                worst_indicators.append((ind, rate, stats["total"]))
    
    if best_indicators:
        best_indicators.sort(key=lambda x: x[1], reverse=True)
        recs.append(f"\n🔥 Best indicators: {best_indicators[0][0][:40]}")
    
    if worst_indicators:
        worst_indicators.sort(key=lambda x: x[1])
        recs.append(f"\n⚠️ Worst indicators: {worst_indicators[0][0][:40]}")
        recs.append("   Pertimbangkan untuk tidak menggunakan indikator ini")
    
    return recs

def generate_signal_reasoning(symbol, direction, indicators):
    """
    Generate human-readable reasoning for why signal triggered
    """
    reasons = []
    
    # RSI Analysis
    rsi = indicators.get("rsi", 50)
    if direction == "LONG" and rsi < 35:
        reasons.append(f"RSI oversold ({rsi:.1f}) - potensi bounce")
    elif direction == "SHORT" and rsi > 65:
        reasons.append(f"RSI overbought ({rsi:.1f}) - potensi pullback")
    
    # MACD Analysis
    macd = indicators.get("macd", 0)
    signal = indicators.get("signal", 0)
    if direction == "LONG" and macd > signal and macd > 0:
        reasons.append(f"MACD bullish crossover (MACD: {macd:.4f} > Signal: {signal:.4f})")
    elif direction == "SHORT" and macd < signal and macd < 0:
        reasons.append(f"MACD bearish crossover (MACD: {macd:.4f} < Signal: {signal:.4f})")
    
    # Volume
    vol = indicators.get("volume_ratio", 1)
    if vol > 1.5:
        reasons.append(f"Volume spike ({vol:.1f}x normal)")
    elif vol < 0.5:
        reasons.append(f"Volume rendah ({vol:.1f}x normal) - risiko rendah likuiditas")
    
    # Bollinger
    bb_position = indicators.get("bb_position", 50)
    if bb_position < 20:
        reasons.append(f"Harga di lower Bollinger Band - oversold")
    elif bb_position > 80:
        reasons.append(f"Harga di upper Bollinger Band - overbought")
    
    # Price action
    price_change = indicators.get("price_change_1h", 0)
    if abs(price_change) > 3:
        reasons.append(f"Strong momentum: {'+' if price_change > 0 else ''}{price_change:.1f}% 1h")
    
    return "; ".join(reasons) if reasons else "Signal meets minimum criteria"

if __name__ == "__main__":
    # Test the logging system
    print("Signal Logging System Ready")
    print(f"Log file: {LOG_FILE}")
    print(f"Evaluation file: {EVAL_FILE}")
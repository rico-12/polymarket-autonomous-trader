#!/usr/bin/env python3
"""
Polymarket Analyst v2.1 - IMPROVED & SCALABLE
Tidak ada lagi hard-coded event (bitboy, gta vi, dll)
Pakai logic general yang sama dengan autonomous_runner.py
"""

import os
import sys
import json
import requests
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console

console = Console()

# ==================== LOAD ENV & TRADER ====================
script_dir = Path(__file__).parent
load_dotenv(script_dir.parent / '.env')

sys_path = str(script_dir)
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

from trader import get_usdc_balance, place_auto_bet

# ==================== GENERAL PROBABILITY ESTIMATOR ====================
def parse_json_safe(data):
    """Safe parse (ganti semua ast.literal_eval)"""
    if isinstance(data, list):
        return data
    if not data or not isinstance(data, str):
        return []
    try:
        return json.loads(data)
    except:
        try:
            return json.loads(data.replace("'", '"'))
        except:
            return []

def estimate_true_prob(market: dict):
    """Logic general (bisa kamu upgrade nanti dengan LLM/CoT)"""
    volume = market.get('volume_24hr', 0) or 0
    outcome_prices = parse_json_safe(market.get('outcomePrices', ''))
    
    if len(outcome_prices) < 2:
        return 0.5, 'LOW'
    
    yes_price = float(outcome_prices[0])
    competitive = market.get('competitive', 0.5)
    
    if volume > 100_000:
        confidence = 'HIGH'
        true_prob = (yes_price + competitive) / 2
    elif volume > 10_000:
        confidence = 'MEDIUM'
        true_prob = (yes_price + competitive) / 2
    else:
        confidence = 'LOW'
        true_prob = 0.5
    
    return round(true_prob, 6), confidence

# ==================== MAIN ANALYSIS ====================
def run_analysis():
    console.rule("[bold blue]🔍 POLYMARKET ANALYST v2.1 - General Mode[/bold blue]")
    
    balance = get_usdc_balance()
    console.log(f"💰 USDC Balance: $[bold cyan]{balance:.2f}[/bold cyan]")
    
    if balance < 5.0:
        console.log("[red]❌ Balance terlalu kecil[/red]")
        return "Balance terlalu kecil"

    # Scan markets
    try:
        url = "https://gamma-api.polymarket.com/markets"
        params = {"active": "true", "closed": "false", "limit": 30, "order": "volume_24hr", "ascending": "false"}
        markets = requests.get(url, params=params, timeout=15).json()[:15]
        console.log(f"📡 Found {len(marksets)} active markets")
    except Exception as e:
        console.log(f"[red]Market fetch error: {e}[/red]")
        return "Gagal fetch market"

    results = []
    for m in markets:
        question = m.get("question", "Unknown")[:80]
        outcome_prices = parse_json_safe(m.get("outcomePrices", []))
        if len(outcome_prices) < 2:
            continue
        
        yes_price = float(outcome_prices[0])
        token_ids = parse_json_safe(m.get("clobTokenIds", []))
        if len(token_ids) < 2:
            continue

        true_prob, confidence = estimate_true_prob(m)
        edge = true_prob - yes_price

        # Decision logic (general, scalable)
        if edge >= 0.08 and confidence in ["HIGH", "MEDIUM"]:
            token_id = token_ids[0]  # YES
            side = "BUY"
            action = f"BUY YES ${1.0} @ {yes_price*100:.2f}% (true {true_prob*100:.1f}%)"
            reason = f"Edge +{edge:.1%} | Confidence {confidence} | Volume ${m.get('volume_24hr',0)/1000:.0f}k"
        elif (1 - true_prob) - (1 - yes_price) >= 0.08 and confidence in ["HIGH", "MEDIUM"]:
            token_id = token_ids[1]  # NO
            side = "BUY"
            action = f"BUY NO ${1.0} @ {(1-yes_price)*100:.2f}% (true {(1-true_prob)*100:.1f}%)"
            reason = f"Edge +{(1-edge):.1%} | Confidence {confidence}"
        else:
            continue

        # Execute bet (max $1)
        bet_result = place_auto_bet(token_id, side, yes_price if side == "BUY" and "YES" in action else (1-yes_price), 1.0)
        
        if bet_result['status'] == 'SUCCESS':
            results.append({
                "market": question,
                "edge": round(edge, 4),
                "action": action,
                "reason": reason,
                "result": bet_result['message']
            })
            console.log(f"[bold green]✅ EDGE FOUND & BET PLACED: {question[:40]}[/bold green]")

        time.sleep(1.5)  # rate limit aman

    # Log
    log_file = script_dir.parent / 'trades_log.md'
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n### {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Analyst v2.1 Run\n")
        for r in results:
            f.write(f"- {r}\n")

    console.log(f"[bold green]🏁 Analyst selesai. {len(results)} edge ditemukan.[/bold green]")
    return results if results else "Tidak ada edge hari ini (mode general aktif)"

# Debug
if __name__ == "__main__":
    run_analysis()
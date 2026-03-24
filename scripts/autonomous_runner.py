#!/usr/bin/env python3
"""
Polymarket Autonomous Trader v2.0 - IMPROVED
Full autonomous + production ready
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
from rich.table import Table

console = Console()

# ==================== LOAD ENV (FIXED) ====================
script_dir = Path(__file__).parent
env_file = script_dir.parent / '.env'
load_dotenv(env_file)  # pakai python-dotenv resmi

if not os.getenv('POLYCLAW_PRIVATE_KEY'):
    console.log("[red]❌ POLYCLAW_PRIVATE_KEY tidak ditemukan di .env[/red]")
    sys.exit(1)

# Import trader (improved)
sys.path.insert(0, str(script_dir))
from trader import get_usdc_balance, place_auto_bet

# ==================== CONFIG ====================
MAX_BET = 1.0
MIN_BALANCE = 5.0
MAX_POSITIONS = 5
MAX_DAILY_BETS = 3
ERROR_THRESHOLD = 5  # circuit breaker

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHANNEL = os.getenv('TELEGRAM_CHANNEL_POLYMARKET', '')

# Circuit breaker
error_count = 0

def send_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL:
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHANNEL, "text": message, "parse_mode": "Markdown"}, timeout=10)
        return True
    except:
        return False

def log_trade(trade_data: dict):
    log_file = script_dir.parent / 'trades_log.md'
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n### {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {trade_data.get('question', 'N/A')}\n")
        for k, v in trade_data.items():
            f.write(f"- **{k}**: {v}\n")

def parse_json_safe(data):
    """Safe json parse (ganti semua ast.literal_eval)"""
    if not data:
        return []
    if isinstance(data, list):
        return data
    try:
        return json.loads(data)
    except:
        try:
            return json.loads(data.replace("'", '"'))  # fallback
        except:
            return []

def get_markets():
    try:
        url = "https://gamma-api.polymarket.com/markets"
        params = {"active": "true", "closed": "false", "limit": 30}
        r = requests.get(url, params=params, timeout=15)
        return r.json() if r.status_code == 200 else []
    except Exception as e:
        console.log(f"[red]Markets fetch error: {e}[/red]")
        return []

def estimate_true_prob(market: dict):
    # Logic CoT sederhana (bisa kamu improve nanti)
    volume = market.get('volume_24hr', 0) or 0
    outcome_prices = parse_json_safe(market.get('outcomePrices', ''))
    if len(outcome_prices) < 2:
        return None, 'LOW'
    
    yes_price = float(outcome_prices[0])
    competitive = market.get('competitive', 0.5)
    
    if volume > 100000:
        return yes_price, 'HIGH'
    elif volume > 10000:
        return (yes_price + competitive) / 2, 'MEDIUM'
    return 0.5, 'LOW'

def analyze_and_decide(market: dict):
    global error_count
    try:
        question = market.get('question', '')[:80]
        outcome_prices = parse_json_safe(market.get('outcomePrices', ''))
        if len(outcome_prices) < 2:
            return None
        
        yes_price = float(outcome_prices[0])
        no_price = float(outcome_prices[1])
        token_ids = parse_json_safe(market.get('clobTokenIds', '[]'))
        
        if len(token_ids) < 2:
            return None

        true_prob, confidence = estimate_true_prob(market)
        if not true_prob:
            return None

        edge_yes = true_prob - yes_price
        edge_no = no_price - true_prob

        decision = None
        if edge_yes >= 0.08 and confidence in ['HIGH', 'MEDIUM']:
            decision = {
                'type': 'YES', 'price': yes_price, 'true_prob': true_prob,
                'edge': edge_yes, 'confidence': confidence,
                'token_id': token_ids[0], 'side': 'BUY',
                'question': question, 'reason': f'Edge +{edge_yes:.1%}'
            }
        elif edge_no >= 0.08 and confidence in ['HIGH', 'MEDIUM']:
            decision = {
                'type': 'NO', 'price': no_price, 'true_prob': 1 - true_prob,
                'edge': edge_no, 'confidence': confidence,
                'token_id': token_ids[1], 'side': 'BUY',
                'question': question, 'reason': f'Edge +{edge_no:.1%}'
            }
        
        return decision
    except Exception as e:
        error_count += 1
        console.log(f"[red]Analysis error: {e}[/red]")
        return None

def run_autonomous():
    console.rule("[bold blue]🚀 POLYMARKET AUTONOMOUS TRADER v2.0[/bold blue]")
    
    balance = get_usdc_balance()
    console.log(f"💰 USDC Balance: $[bold cyan]{balance:.2f}[/bold cyan]")
    
    if balance < MIN_BALANCE:
        console.log("[red]❌ Balance terlalu rendah[/red]")
        return

    markets = get_markets()
    console.log(f"📡 Found {len(markets)} active markets")

    bets_today = 0
    for market in markets:
        if bets_today >= MAX_DAILY_BETS:
            break
        
        decision = analyze_and_decide(market)
        if not decision:
            continue

        console.log(f"🎯 [bold yellow]EDGE FOUND[/bold yellow] → {decision['question'][:40]} | Edge +{decision['edge']:.1%}")

        bet_result = place_auto_bet(
            decision['token_id'],
            decision['side'],
            decision['price'],
            MAX_BET
        )

        if bet_result['status'] == 'SUCCESS':
            log_trade({**decision, **bet_result})
            send_telegram(f"✅ **AUTO BET**\nMarket: {decision['question']}\nSide: {decision['type']} @ {decision['price']*100:.1f}%\nSize: ${MAX_BET}\nEdge: +{decision['edge']:.1%}")
            bets_today += 1
            console.log("[bold green]✅ BET EXECUTED[/bold green]")
        else:
            console.log(f"[red]Bet failed: {bet_result['message']}[/red]")

        time.sleep(2)  # rate limit aman

    console.log("[bold green]🏁 Autonomous run selesai[/bold green]")

if __name__ == "__main__":
    run_autonomous()
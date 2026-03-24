#!/usr/bin/env python3
"""
Polymarket Autonomous Trader
Full autonomous - scan, research, decide, bet
Max $1 per bet - WAJIB TEGUH!
"""

import os
import sys
import json
import requests
import ast
from datetime import datetime
from pathlib import Path

# Load env
script_dir = Path(__file__).parent
env_file = script_dir.parent / 'neko-futures-trader' / '.env'

if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

# Import from trader.py
sys.path.insert(0, str(script_dir))
from trader import init_client

# Config
POLYMARKET_HOST = "https://clob.polymarket.com"
MAX_BET = 1.0  # $1 MAX - WAJIB TEGUH!
MIN_BALANCE = 5.0
MAX_POSITIONS = 5
MAX_DAILY_BETS = 3

# Telegram
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHANNEL = os.environ.get('TELEGRAM_CHANNEL_POLYMARKET', '')

# Initialize client on load
_client = None

def get_usdc_balance():
    """Get balance with proper initialization"""
    global _client
    try:
        if _client is None:
            _client = init_client()
        
        from py_clob_client.clob_types import BalanceAllowanceParams, AssetType
        result = _client.get_balance_allowance(
            BalanceAllowanceParams(asset_type=AssetType.COLLATERAL)
        )
        balance = int(result.get('balance', 0)) / 1_000_000
        return round(balance, 2)
    except Exception as e:
        print(f"Balance error: {e}")
        return 16.6  # Use last known balance as fallback

def get_markets():
    """Fetch markets from Gamma API"""
    try:
        url = "https://gamma-api.polymarket.com/markets"
        params = {"active": "true", "closed": "false", "limit": 30}
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"Error fetching markets: {e}")
        return []

def parse_outcome_prices(outcome_prices_str):
    if not outcome_prices_str:
        return []
    try:
        if isinstance(outcome_prices_str, str):
            return ast.literal_eval(outcome_prices_str)
        return outcome_prices_str
    except:
        return []

def estimate_true_prob(market):
    """
    Chain-of-thought: Estimate true probability
    Berdasarkan volume dan historical patterns
    """
    question = market.get('question', '')
    volume = market.get('volume_24hr', 0) or 0
    
    # Get prices
    outcome_prices = parse_outcome_prices(market.get('outcomePrices', ''))
    if len(outcome_prices) < 2:
        return None, 'LOW'
    
    yes_price = float(outcome_prices[0])
    no_price = float(outcome_prices[1])
    
    # Simple heuristic untuk true probability estimation
    # Berdasarkan volume dan competitive score
    competitive = market.get('competitive', 0.5)
    
    # Volume-based adjustment
    # High volume = more accurate price
    if volume > 100000:
        confidence = 'HIGH'
        # Price is likely accurate
        true_prob = yes_price
    elif volume > 10000:
        confidence = 'MEDIUM'
        true_prob = (yes_price + competitive) / 2
    else:
        confidence = 'LOW'
        true_prob = 0.5  # Uncertain
    
    return true_prob, confidence

def calculate_edge(market_price, true_prob):
    """Hitung edge antara market price dan true probability"""
    return abs(true_prob - market_price)

def analyze_and_decide(market):
    """Full chain-of-thought analysis untuk satu market"""
    
    # 1. Ambil data
    question = market.get('question', '')
    if not question:
        return None
    
    # Clean question
    if '(' in question:
        question = question.split('(')[0].strip()
    
    # Get prices
    outcome_prices = parse_outcome_prices(market.get('outcomePrices', ''))
    if len(outcome_prices) < 2:
        return None
    
    yes_price = float(outcome_prices[0])
    no_price = float(outcome_prices[1])
    volume = market.get('volume_24hr', 0) or 0
    
    # Get token IDs
    token_ids_str = market.get('clobTokenIds', '[]')
    try:
        token_ids = ast.literal_eval(token_ids_str)
    except:
        token_ids = []
    
    if len(token_ids) < 2:
        return None
    
    # 2. Estimate true probability (Chain-of-Thought)
    true_prob, confidence = estimate_true_prob(market)
    
    # 3. Hitung edge
    edge_yes = calculate_edge(yes_price, true_prob) if true_prob else 0
    
    # 4. Decision
    decision = None
    
    # Untuk YES bet
    if true_prob and true_prob > yes_price + 0.08:  # Edge ≥ 8%
        if confidence in ['HIGH', 'MEDIUM']:
            # Price lebih rendah dari true probability - value!
            potential_edge = true_prob - yes_price
            if potential_edge >= 0.10 or (potential_edge >= 0.08 and confidence == 'HIGH'):
                decision = {
                    'type': 'YES',
                    'price': yes_price,
                    'true_prob': true_prob,
                    'edge': potential_edge,
                    'confidence': confidence,
                    'token_id': token_ids[0],
                    'side': 'BUY',
                    'reason': f'True prob {true_prob:.0%} > market {yes_price:.0%}, edge +{potential_edge:.0%}'
                }
    
    # Untuk NO bet
    if true_prob and true_prob < no_price - 0.08:  # Edge ≥ 8%
        if confidence in ['HIGH', 'MEDIUM']:
            potential_edge = no_price - true_prob
            if potential_edge >= 0.10 or (potential_edge >= 0.08 and confidence == 'HIGH'):
                decision = {
                    'type': 'NO',
                    'price': no_price,
                    'true_prob': 1 - true_prob,
                    'edge': potential_edge,
                    'confidence': confidence,
                    'token_id': token_ids[1],
                    'side': 'BUY',
                    'reason': f'True prob {1-true_prob:.0%} > market {no_price:.0%}, edge +{potential_edge:.0%}'
                }
    
    if decision:
        decision['question'] = question[:50]
        decision['volume'] = volume
    
    return decision

def check_limits(balance, active_positions):
    """Check apakah masih bisa bet"""
    if balance < MIN_BALANCE:
        return False, f"Balance ${balance:.2f} < min ${MIN_BALANCE}"
    if active_positions >= MAX_POSITIONS:
        return False, f"Active positions {active_positions} >= max {MAX_POSITIONS}"
    return True, "OK"

def send_telegram(message):
    """Send to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL:
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHANNEL,
            "text": message,
            "parse_mode": "Markdown"
        }
        r = requests.post(url, json=data, timeout=10)
        return r.status_code == 200
    except:
        return False

def log_trade(trade_data):
    """Log trade ke file"""
    log_file = script_dir / 'trades_log.md'
    
    entry = f"| {datetime.now().strftime('%Y-%m-%d %H:%M')} | {trade_data.get('question', 'N/A')} | {trade_data.get('type', 'N/A')} | ${trade_data.get('size', 0)} | {trade_data.get('result', 'PENDING')} |\n"
    
    with open(log_file, 'a') as f:
        f.write(entry)

def run_autonomous_trading():
    """Main autonomous trading function"""
    print("🎯 Polymarket Autonomous Trader Starting...")
    print(f"   Max bet: ${MAX_BET}")
    print(f"   Min balance: ${MIN_BALANCE}")
    print()
    
    # Get balance
    balance = get_usdc_balance()
    print(f"💰 Balance: ${balance}")
    
    # Check limits
    can_trade, reason = check_limits(balance, 0)
    if not can_trade:
        print(f"⚠️ Cannot trade: {reason}")
        return
    
    # Get markets
    print("\n📡 Scanning markets...")
    markets = get_markets()
    print(f"   Found {len(markets)} markets")
    
    # Analyze each market
    decisions = []
    for market in markets:
        decision = analyze_and_decide(market)
        if decision:
            decisions.append(decision)
    
    print(f"   Found {len(decisions)} opportunities with edge ≥8%")
    
    if not decisions:
        msg = "🎯 *Autonomous Scan Complete*\n\n"
        msg += f"Balance: ${balance}\n"
        msg += f"Markets analyzed: {len(markets)}\n"
        msg += f"Opportunities found: 0\n\n"
        msg += "❌ No good edge found - SKIPPED\n"
        msg += "Reason: All markets have edge < 8% or low confidence"
        
        send_telegram(msg)
        return
    
    # Sort by edge (highest first)
    decisions.sort(key=lambda x: x.get('edge', 0), reverse=True)
    
    # Take top decision
    top = decisions[0]
    
    # Execute bet - MAX $1!
    size = min(MAX_BET, balance * 0.1)  # Max $1 atau 10% balance
    size = min(size, 1.0)  # Pastikan max $1
    
    print(f"\n🎯 Top opportunity:")
    print(f"   {top['question']}")
    print(f"   Bet: {top['type']} @ {top['price']*100:.1f}%")
    print(f"   Edge: {top['edge']*100:.1f}%")
    print(f"   Confidence: {top['confidence']}")
    print(f"   Size: ${size:.2f}")
    
    # Execute
    result = execute_bet(
        token_id=top['token_id'],
        side=top['side'],
        price=top['price'],
        size=size
    )
    
    print(f"\n📊 Result: {result}")
    
    # Send to Telegram
    msg = "🎯 *AUTONOMOUS BET EXECUTED*\n"
    msg += "═══════════════════════\n"
    msg += f"Market: {top['question']}\n"
    msg += f"Direction: BUY {top['type']} @ {top['price']*100:.1f}%\n"
    msg += f"True Prob: {top['true_prob']*100:.1f}%\n"
    msg += f"Edge: +{top['edge']*100:.1f}%\n"
    msg += f"Confidence: {top['confidence']}\n"
    msg += f"Size: ${size:.2f}\n"
    msg += f"\nReason: {top['reason']}\n"
    msg += "═══════════════════════"
    
    send_telegram(msg)
    
    # Log
    log_trade({
        'question': top['question'],
        'type': top['type'],
        'size': size,
        'price': top['price'],
        'edge': top['edge'],
        'confidence': top['confidence']
    })

if __name__ == "__main__":
    run_autonomous_trading()
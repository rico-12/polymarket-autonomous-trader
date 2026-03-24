#!/usr/bin/env python3
"""
Polymarket Scanner - Using Gamma API (Working!)
Direct API - Self-built - No Nansen
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path
import ast

# === CONFIG ===
script_dir = Path(__file__).parent
env_file = script_dir / '.env'

if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHANNEL_POLYMARKET = os.environ.get('TELEGRAM_CHANNEL_POLYMARKET', '')

# Gamma API - Working!
GAMMA_API = "https://gamma-api.polymarket.com/markets"

# Filter: ONLY Crypto & Sports
CRYPTO_KEYWORDS = ['bitcoin', 'btc', 'eth', 'ethereum', 'solana', 'crypto', 'token', 'coin', 'price', 'dogecoin', 'shiba', 'pepe', 'memecoin', 'altcoin', 'binance', 'exchange']
SPORTS_KEYWORDS = ['nba', 'nfl', 'football', 'soccer', 'tennis', 'ufc', 'mma', 'boxing', 'golf', 'f1', 'formula', 'championship', 'game', 'match', 'winner', 'league', 'cup', 'qualify', 'world cup', 'euro', 'premier', 'laliga', 'serie', 'bundesliga', 'mlb', 'hockey', 'basketball', 'volleyball', 'atlético', 'real madrid', 'barcelona', 'manchester', 'liverpool', 'chelsea', 'arsenal', 'juventus', 'milan', 'inter', 'bayern', 'psg', 'messi', 'ronaldo', 'mbappe', 'haaland']

def is_crypto_or_sports(question):
    """Filter: only crypto or sports"""
    q = question.lower()
    return any(k in q for k in CRYPTO_KEYWORDS) or any(k in q for k in SPORTS_KEYWORDS)

def fetch_markets():
    """Fetch markets from Gamma API"""
    try:
        # Simple params - Gamma API is picky
        params = {
            "active": "true",
            "closed": "false",
            "limit": 30
        }
        
        response = requests.get(GAMMA_API, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                return data[:30]
            elif isinstance(data, dict) and 'data' in data:
                return data['data'][:30]
        
        return []
    except Exception as e:
        print(f"Fetch error: {e}")
        return []

def parse_outcome_prices(outcome_prices_str):
    """Parse outcome prices from string to list"""
    if not outcome_prices_str:
        return []
    
    try:
        # Try to parse as JSON string
        if isinstance(outcome_prices_str, str):
            return ast.literal_eval(outcome_prices_str)
        return outcome_prices_str
    except:
        return []

def analyze_market(market):
    """Analyze a market and generate signals"""
    try:
        # Skip closed markets
        if market.get('closed', False):
            return None
        
        # Get question
        question = market.get('question', '')
        if not question:
            return None
        
        # FILTER: Only crypto or sports
        if not is_crypto_or_sports(question):
            return None
        
        # Clean question - remove date at end
        if '(' in question:
            question = question.split('(')[0].strip()
        
        # Get volume - use volume24hr
        volume_24h = market.get('volume_24hr', 0) or market.get('volume24hr', 0) or 0
        
        # Get outcome prices
        outcome_prices_str = market.get('outcomePrices', '')
        outcome_prices = parse_outcome_prices(outcome_prices_str)
        
        if not outcome_prices or len(outcome_prices) < 2:
            return None
        
        # Parse prices
        try:
            yes_price = float(outcome_prices[0])
            no_price = float(outcome_prices[1])
        except (ValueError, TypeError, IndexError):
            return None
        
        # Calculate probabilities
        yes_prob = yes_price * 100
        no_prob = no_price * 100
        
        # Generate signals
        signals = []
        
        # YES signal
        if yes_prob >= 55:
            signals.append({
                'outcome': 'YES',
                'price': yes_price,
                'probability': yes_prob,
                'signal': 'YES'
            })
        elif yes_prob >= 45:
            signals.append({
                'outcome': 'YES',
                'price': yes_price,
                'probability': yes_prob,
                'signal': 'LEAN YES'
            })
        
        # NO signal
        if no_prob >= 55:
            signals.append({
                'outcome': 'NO',
                'price': no_price,
                'probability': no_prob,
                'signal': 'NO'
            })
        elif no_prob >= 45:
            signals.append({
                'outcome': 'NO',
                'price': no_price,
                'probability': no_prob,
                'signal': 'LEAN NO'
            })
        
        if not signals:
            return None
        
        # Determine urgency based on end date
        end_date = market.get('endDate', '')
        urgency = '📅'
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                hours_left = (end_dt - datetime.now()).total_seconds() / 3600
                
                if hours_left > 0 and hours_left < 24:
                    urgency = '🔥'
                elif hours_left > 0 and hours_left < 72:
                    urgency = '⚡'
                elif hours_left <= 0:
                    return None  # Skip expired
            except:
                pass
        
        return {
            'question': question[:45],
            'volume_24h': volume_24h,
            'urgency': urgency,
            'signals': signals[:2],
            'end_date': end_date[:10] if end_date else 'N/A'
        }
        
    except Exception as e:
        print(f"Analyze error: {e}")
        return None

def format_message(markets_data):
    """Format message for Telegram"""
    if not markets_data:
        return "❌ No good signals found. Will retry next scan."
    
    msg = "🎯 *POLYMARKET SCAN*\n"
    msg += "═" * 35 + "\n"
    msg += f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC\n"
    msg += "📡 Source: Gamma API (Working!)\n\n"
    
    for market in markets_data[:8]:
        q = market.get('question', 'Unknown')
        vol = market.get('volume_24h', 0)
        end = market.get('end_date', 'N/A')
        
        # Format volume
        if vol >= 1_000_000:
            vol_str = f"${vol/1_000_000:.1f}M"
        elif vol >= 1_000:
            vol_str = f"${vol/1_000:.0f}K"
        else:
            vol_str = f"${vol:.0f}"
        
        msg += f"{market['urgency']} *{q}*\n"
        msg += f"   💰 Vol: {vol_str} | 📅 {end}\n"
        
        for sig in market.get('signals', []):
            emoji = "✅" if sig['signal'] == 'YES' else ("🔶" if sig['signal'] == 'LEAN YES' else ("❌" if sig['signal'] == 'NO' else "🔶"))
            prob = sig['probability']
            outcome = sig['outcome']
            msg += f"   {emoji} {outcome}: {prob:.1f}%\n"
        
        msg += "\n"
    
    msg += "═" * 35 + "\n"
    msg += "🔧 Built with our own system!"
    
    return msg

def send_telegram(message):
    """Send to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_POLYMARKET:
        print("Telegram not configured")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHANNEL_POLYMARKET,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        r = requests.post(url, json=data, timeout=10)
        if r.status_code == 200:
            print("✅ Posted to Polymarket channel!")
            return True
        else:
            print(f"Error: {r.status_code}")
            return False
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def main():
    print("🎯 Polymarket Scanner v3 - Gamma API!")
    print("-" * 35)
    
    # Fetch from Gamma API
    print("📡 Fetching from Gamma API...")
    markets = fetch_markets()
    print(f"   Found {len(markets)} markets")
    
    if not markets:
        print("❌ No data - will try again next time")
        return
    
    # Analyze each market
    analyzed = []
    for market in markets:
        result = analyze_market(market)
        if result:
            analyzed.append(result)
    
    print(f"   {len(analyzed)} markets with signals")
    
    # Send to Telegram
    if analyzed:
        msg = format_message(analyzed)
        send_telegram(msg)
    else:
        print("   No actionable signals")

if __name__ == "__main__":
    main()
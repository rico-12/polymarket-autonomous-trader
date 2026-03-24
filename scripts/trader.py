from py_clob_client.client import ClobClient
from py_clob_client.clob_types import BalanceAllowanceParams, AssetType, OrderArgs
import os
import time
from rich.console import Console

console = Console()

POLYMARKET_HOST = "https://clob.polymarket.com"
MAX_RETRIES = 3

# Global client (singleton)
_client = None

def init_client():
    """Initialize client sekali saja"""
    global _client
    if _client is None:
        console.log("[bold green]🔌 Initializing Polymarket client...[/bold green]")
        _client = ClobClient(
            host=POLYMARKET_HOST,
            key=os.getenv('POLYCLAW_PRIVATE_KEY'),
            chain_id=137,
            signature_type=2  # gasless
        )
        _client.set_api_creds(_client.create_or_derive_api_creds())
    return _client

def get_usdc_balance() -> float:
    """Get USDC balance dengan retry"""
    for attempt in range(MAX_RETRIES):
        try:
            client = init_client()
            result = client.get_balance_allowance(
                BalanceAllowanceParams(asset_type=AssetType.COLLATERAL)
            )
            balance = int(result.get('balance', 0)) / 1_000_000
            return round(balance, 6)  # precision USDC
        except Exception as e:
            console.log(f"[yellow]Balance attempt {attempt+1} failed: {e}[/yellow]")
            if attempt == MAX_RETRIES - 1:
                console.log("[red]❌ Failed to get balance after retries[/red]")
                return 0.0
            time.sleep(2 ** attempt)  # exponential backoff
    return 0.0

def place_auto_bet(token_id: str, side: str, price: float, size: float):
    """Place bet dengan validasi + retry + circuit breaker"""
    if size > 1.0:
        size = 1.0  # MAX $1 HARD LIMIT
    if size < 0.01:
        return {'status': 'ERROR', 'message': 'Size terlalu kecil (< $0.01)'}

    price = round(price, 6)  # Polymarket precision

    for attempt in range(MAX_RETRIES):
        try:
            client = init_client()
            order_args = OrderArgs(
                token_id=token_id,
                price=price,
                size=size,
                side=side.upper()
            )
            order = client.create_and_post_order(order_args=order_args)
            console.log(f"[bold green]✅ BET SUCCESS: {side} ${size} @ {price*100:.2f}%[/bold green]")
            return {'status': 'SUCCESS', 'message': f'✅ AUTO BET {side} ${size} @ {price*100:.2f}%', 'order': order}
        except Exception as e:
            console.log(f"[yellow]Bet attempt {attempt+1} failed: {str(e)[:100]}[/yellow]")
            if attempt == MAX_RETRIES - 1:
                return {'status': 'ERROR', 'message': str(e)}
            time.sleep(3 ** attempt)
    return {'status': 'ERROR', 'message': 'Max retries reached'}
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import BalanceAllowanceParams, AssetType, OrderArgs
import os

POLYMARKET_HOST = "https://clob.polymarket.com"

def init_client():
    client = ClobClient(
        host=POLYMARKET_HOST,
        key=os.getenv('POLYCLAW_PRIVATE_KEY'),
        chain_id=137,
        signature_type=2  # gasless
    )
    # 🔥 Setup L2 creds
    client.set_api_creds(client.create_or_derive_api_creds())
    return client

def get_usdc_balance() -> float:
    """Auto baca USDC balance Polymarket (yang dipakai buat trading)"""
    try:
        client = init_client()
        result = client.get_balance_allowance(
            BalanceAllowanceParams(asset_type=AssetType.COLLATERAL)
        )
        balance = int(result.get('balance', 0)) / 1_000_000
        return round(balance, 2)
    except Exception as e:
        return f"ERROR: {str(e)[:100]}"

def place_auto_bet(token_id: str, side: str, price: float, size: float):
    client = init_client()
    try:
        # Create OrderArgs
        order_args = OrderArgs(
            token_id=token_id,
            price=price,
            size=size,
            side=side.upper()
        )
        
        # Create and post order
        order = client.create_and_post_order(order_args=order_args)
        
        return {'status': 'SUCCESS', 'message': f'✅ AUTO BET {side} {size} USDC @ {price*100}%', 'order': order}
    except Exception as e:
        return {'status': 'ERROR', 'message': str(e)}
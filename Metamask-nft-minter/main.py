from utils import AccountEVM
from utils.constants import DEFAULT_PRIVATE_KEYS
from loguru import logger
from config import RANDOMIZE
import sys
from utils.constants import logo, PROJECT, DEFAULT_LOGS_FILE, LOGS_SIZE
import random
import asyncio
from curl_cffi import requests
from utils import error_handler, pad32Bytes, pad96Bytes, sync_sleep

CONTRACT = '0x334eD1615263B292188D37b8d84662498977eDAA'
URL = 'https://public-api.phosphor.xyz/v1/purchase-intents'
PAYLOAD_BASE = {
    'listing_id': "0ebc79c4-9a87-43fa-8889-8add7d0ba700",
    'origin': "METAMASK_PORTFOLIO",
    'provider': "MINT_VOUCHER",
    'quantity': 1
}

@error_handler('Runner | Get Signature')
def get_tx_data(account:AccountEVM):
    payload = PAYLOAD_BASE.copy()
    payload['buyer'] = {
        'eth_address': account.address
    }
    response = requests.post(
        URL,
        impersonate="chrome", 
        headers={
            'origin': 'https://portfolio.metamask.io',
            'referer': 'https://portfolio.metamask.io/'
        }, 
        json=payload,
        proxies=account.proxy
    )
    response.raise_for_status()
    sig = response.json()['data']['signature']
    exp = response.json()['data']['voucher']['expiry']
    data =( '0x899cb148'
            '0000000000000000000000000000000000000000000000000000000000000040'
            '00000000000000000000000000000000000000000000000000000000000001a0'
            '0000000000000000000000000000000000000000000000000000000000000100'
            '0000000000000000000000000000000000000000000000000000000000000120'
            '0000000000000000000000000000000000000000000000000000000000000001'
            '0000000000000000000000000000000000000000000000000000000000000001'
            f"{pad32Bytes(hex(exp))}"
            '0000000000000000000000000000000000000000000000000000000000000000'
            '0000000000000000000000000000000000000000000000000000000000000000'
            '0000000000000000000000000000000000000000000000000000000000000140'
            '0000000000000000000000000000000000000000000000000000000000000000'
            '0000000000000000000000000000000000000000000000000000000000000000'
            '0000000000000000000000000000000000000000000000000000000000000000'
            '0000000000000000000000000000000000000000000000000000000000000041'
            f"{pad96Bytes(sig, 'right')}"
        )
    return data

def runner(): 

    with open(DEFAULT_PRIVATE_KEYS, 'r', encoding='utf-8') as f:
        private_keys = f.read().splitlines()
    if RANDOMIZE:
        random.shuffle(private_keys)
    
    accounts = [AccountEVM('LINEA', private_key) for private_key in private_keys]

    for account in accounts:
        data = get_tx_data(account)
        balance = account.get_erc20_balance(CONTRACT, True)
        if balance > 0: 
            logger.info(f'{account.address}: already has NFT, skipping to next account')
            continue
        if not data:
            logger.warning(f'{account.address}: failed to get tx data, skipping to next account')
            continue
        tx = {
            "from": account.address,
            "to": CONTRACT,
            "data": data,
            "value": 0
        }
        sent = account.send_tx(tx)
        if sent:
            sync_sleep('Account', account.address)
        else:
            logger.warning(f'{account.address}: failed to send tx, skipping to next account')

logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> |  <level>{message}</level>",
    colorize=True,
    
)
logger.add(DEFAULT_LOGS_FILE, rotation=LOGS_SIZE)
logger.opt(raw = True).info(logo)

if __name__ == '__main__':
    runner()
# MAIN SETTINGS =================================================================

ACCOUNTS_DELAY = [10,120] #задержка между аккаунтами
ACTIONS_DELAY = [1,20] #задержка между действиями
USE_PROXIES_IN_WEB3 = False #использовать прокси при подключении к RPC 
RANDOMIZE = False #если True, то будет рандомизировать порядок аккаунтов 


# OTHER SETTINGS =================================================================

RPC = {
    'LINEA': 'https://rpc.linea.build'
}

MAX_ETH_GWEI = 100
ERR_ATTEMPTS = 5
TX_RETRIES = 3
MAX_TX_WAIT = 500
GAS_MULT = 1.2
GAS_PRICE_MULT = 1.5
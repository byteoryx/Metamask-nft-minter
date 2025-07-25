from loguru import logger
from config import ERR_ATTEMPTS, ACCOUNTS_DELAY, ACTIONS_DELAY
from .constants import DEFAULT_PRIVATE_KEYS, DEFAULT_PROXIES
import sys
import time
import asyncio
import random
import traceback
import math
from typing import Literal
from stringtools.generators import Nick

def intToDecimal(qty, decimal):
    return int(qty * int("".join(["1"] + ["0"]*decimal)))

def decimalToInt(price, decimal):
    return price/ int("".join((["1"]+ ["0"]*decimal)))

def clear_file(file):
    file_to_clear = open(file,'w', encoding="utf-8")
    file_to_clear.close()

def write_to_file(file, result):
    with open(file, "a", encoding="utf-8") as file:
        file.write(str(result) + '\n')

def round_decimal_value(value:int, rounding:int): 

    value = int(value)
    l = len(str(value))

    value = str(value)[0] if rounding == 0 else str(value)[:rounding] 
    if int(value[-1]) > 5: 
        value = int(value)+1

    while len(str(value)) < l: 
        value = str(value) + "0"

    return int(value)

def round_floor(value:int | float, rounding:int): 
    value = float(value)
    multiplier = 10 ** rounding
    return math.floor(value * multiplier) / multiplier

def generate_amount_in_range(range:list, rounding:list):

    n = random.randrange(rounding[0], rounding[1])
    amount = random.uniform(range[0], range[1])
    amount = round(amount, n)

    return amount

def generate_nickname(length:list[int, int] = [4,10], numbers:list[int,int] = [0,3], disable_numbers:bool = False, disable_spacer:bool = False):
    n  = Nick()
    n.set_length(random.randrange(length[0],length[1]))
    name = n.generate()
    
    if bool(random.getrandbits(1)) and not disable_numbers: 
        use_spacer = bool(random.getrandbits(1))
        if use_spacer and not disable_spacer:
            spacer = random.choice(['_', '-'])
            name = name+spacer
        name = name+str(random.randrange(numbers[0],numbers[1]))
    capitalize = random.getrandbits(1)
    if capitalize:
        name = name[0].upper() + name[1:]
    return name

def pad32Bytes(data):
      
      s = data[2:] if data[:2] == '0x' else data
      while len(s) < 64 :
        s = "0" + s
      return s

def pad96Bytes(data, side: Literal['left', 'right'] = 'left'):
      s = data[2:] if data[:2] == '0x' else data
      while len(s) < 192 :
        if side == 'left':
            s = "0" + s
        else:
            s += "0"
      return s


def error_handler(error_msg, retries = ERR_ATTEMPTS):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i in range(0, retries):
                try: 
                    return func(*args, **kwargs)
                except Exception as e:
                    # Get the traceback info
                    tb = traceback.extract_tb(e.__traceback__)
                    # Last frame is where the exception occurred
                    last_frame = tb[-1]
                    file_name = last_frame.filename
                    file_name = file_name.split('\\')[-1].split('/')[-1] 
                    line_no = last_frame.lineno
                    
                    # Log error with file and line info
                    logger.error(f"{error_msg}: {str(e)} in {file_name}, line {line_no}")
                    logger.info(f'Retrying in 10 sec. Attempts left: {ERR_ATTEMPTS-i}')
                    time.sleep(10)
                    if i == retries-1: 
                        return 0
        return wrapper
    return decorator

def get_proxy(private_key): 

    check_proxy()

    with open(DEFAULT_PROXIES, 'r') as f: 
        proxies = f.read().splitlines()
        if len(proxies) == 0:
            return None
        
    with open(DEFAULT_PRIVATE_KEYS, 'r') as f: 
        privates = f.read().splitlines()
            
    n = privates.index(str(private_key))
    proxy = proxies[n]
    proxy = {
        'http': f'http://{proxy}',
        'https':f'http://{proxy}'
    }
    return proxy

def get_token(private_key:str, token_path:str):
    with open(DEFAULT_PRIVATE_KEYS, 'r', encoding="utf-8") as f: 
        privates = f.read().splitlines()
    n = privates.index(private_key)

    with open(token_path, 'r', encoding="utf-8") as f: 
        tokens = f.read().splitlines()

    if len(tokens) < len(privates):
        logger.error(f'Tokens in {token_path} do not match private keys')
        sys.exit()

    return tokens[n]

def check_proxy():

    with open(DEFAULT_PROXIES, 'r') as f: 
        proxies = f.read().splitlines()
    with open(DEFAULT_PRIVATE_KEYS, 'r') as f: 
        stark_privates = f.read().splitlines()

    if len(proxies) < len(stark_privates) and len(proxies) != 0:
        logger.error('Proxies do not match private keys')
        sys.exit()

def async_error_handler(error_msg, retries=ERR_ATTEMPTS):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            for i in range(0, retries):
                try:
                    return await func(*args, **kwargs)
                
                except TimeoutError as e:
                    # Get the traceback info for timeout errors
                    tb = traceback.extract_tb(e.__traceback__)
                    # Last frame is where the exception occurred
                    last_frame = tb[-1]
                    file_name = last_frame.filename
                    file_name = file_name.split('\\')[-1].split('/')[-1] 
                        
                    line_no = last_frame.lineno
                    
                    logger.error(f"{error_msg}: TimeoutError - {str(e)[:250]} in {file_name}, line {line_no}")
                    if i == retries - 1:
                        return 0
                    logger.info(f"TimeoutError: Retrying in 10 sec. Attempts left: {retries-i-1}")
                    await asyncio.sleep(10)

                except Exception as e:
                    # Get the traceback info
                    tb = traceback.extract_tb(e.__traceback__)
                    # Last frame is where the exception occurred
                    last_frame = tb[-1]
                    file_name = last_frame.filename
                    file_name = file_name.split('\\')[-1].split('/')[-1] 
                    line_no = last_frame.lineno
                    
                    logger.error(f"{error_msg}: {str(e)} in {file_name}, line {line_no}")
                    if i == retries - 1:
                        return 0
                    logger.info(f"Retrying in 10 sec. Attempts left: {retries-i-1}")
                    await asyncio.sleep(10)
                    
        return wrapper
    return decorator

async def sleep(type_delay = Literal['Account', 'Action'], account_address: str | None = None): 
    match type_delay: 
        case 'Account': 
            sleep_time = ACCOUNTS_DELAY
        case 'Action': 
            sleep_time = ACTIONS_DELAY
        case _: 
            raise Exception('Wrong sleep type in delay function (async sleep)')
    sleep_time = random.uniform(*sleep_time)
    logger.info(f'{account_address + ": " if account_address else ""}waiting {int(sleep_time)} seconds before next {type_delay}')
    await asyncio.sleep(sleep_time)

def sync_sleep(type_delay = Literal['Account', 'Action'], account_address: str | None = None): 
    match type_delay: 
        case 'Account': 
            sleep_time = ACCOUNTS_DELAY
        case 'Action': 
            sleep_time = ACTIONS_DELAY
        case _: 
            raise Exception('Wrong sleep type in delay function (async sleep)')
    sleep_time = random.uniform(*sleep_time)
    logger.info(f'{account_address + ": " if account_address else ""}waiting {int(sleep_time)} seconds before next {type_delay}')
    time.sleep(sleep_time)
import os
import sys
import json
import logging, logging.handlers
from datetime import datetime
import requests

import json_log_formatter
import statistics

from dotenv import load_dotenv
  
Log_Format = "%(levelname)s %(asctime)s - %(message)s"

logging.basicConfig(stream = sys.stdout, 
                    filemode = "w",
                    format = Log_Format, 
                    level = logging.INFO)


formatter = json_log_formatter.JSONFormatter()

json_handler = logging.StreamHandler()
json_handler.setFormatter(formatter)

logger = logging.getLogger()
#logger.addHandler(json_handler)

load_dotenv()
RIPPLED_SERVER_URL = os.getenv('RIPPLED_SERVER_URL')
ACCOUNT = os.getenv('ACCOUNT')
CURRENCY = os.getenv('CURRENCY')
COINSTAT_API_URL = os.getenv("COINSTAT_API_URL")
CONST_XRP = 'XRP'

def main():
    XRP_PER_FIAT = get_xrp_fiat_ratio(CURRENCY)
    result = []
    #  get_server_info() 
    result = { "account" : ACCOUNT,
                "balance_xrp" : 0,
                "balance_baselines_xrp" : 0,
                "balance_total" : 0,
                "balance_total_fiat" : 0,
                "params" : {
                    "price_per_xrp" : XRP_PER_FIAT,
                    "fiat_currency" : CURRENCY
                },
                "date" : datetime.now().isoformat(),
                "lines" : []
            }

    account_info = get_account_info(ACCOUNT).json()
    result['balance_xrp'] = float(account_info['result']['account_data']['Balance']) / 1000000
    
    
    account_lines = get_account_lines(ACCOUNT).json()
    logger.debug(account_lines)

    #We are only interested in tokens with a balance above 0.
    filtered_lines = filter(lambda x: float(x['balance']) > 0, account_lines['result']['lines'])

    for account_line in filtered_lines:
        token = account_line.get('currency')
        #convert the hex token names in ascii
        if len(token) > 3:
            currency_readable = bytes.fromhex(token.rstrip("0")).decode('utf-8')
        else:
            currency_readable = token
        
       
        xrp_per_token = get_avg_price_for_token( token, account_line['account'])
        logger.info(f'Calculated average ratio for {currency_readable} to XRP: {xrp_per_token}')
        balance_xrp = xrp_per_token * float(account_line['balance'])
        balance_fiat = round(balance_xrp * XRP_PER_FIAT,2)
       

        result['lines'].append(
                {
                    'currency' : account_line.get('currency'),
                    'currency_readable' : currency_readable,
                    'issuer_account' : account_line.get('account'),
                    'balance' : account_line.get('balance'),  
                    'balance_xrp' : balance_xrp,
                    'balance_fiat' : balance_fiat,
                    'currency_fiat' : CURRENCY
                })

        
        result['balance_baselines'] = float(result['balance_baselines']) + balance_xrp
        result['balance_total'] = float(result['balance_baselines']) + float(result['balance_xrp'])
        result['balance_total_fiat'] = round(float(result['balance_total']) * XRP_PER_FIAT,2)

    with open('out/json_result.json',"w") as f:
        f.write(json.dumps(result, indent=4))
        

def get_avg_price_for_token(token, issuer_account):
    offers = get_offers_for_token(token, issuer_account).json()
    xrp_per_token_list = []
    for offer in offers['result']['offers']:
        taker_gets = float(offer['TakerGets'])
        taker_pays = float(offer['TakerPays']['value'])
        xrp_per_token_list.append(taker_gets/taker_pays/1000000)
        logger.debug(f'Analysing offers. Curency: {token}, ratio: {taker_gets/taker_pays/1000000} | GET {taker_gets}, PAY {taker_pays}')

    return statistics.mean(xrp_per_token_list)
    

  

def get_server_info():
    logger.info('Getting server info for account')
    data = {
        "method": "server_info",
        "params": [
            {
                "api_version": 1
            }
        ]
    }
    return query_ledger_api(data)

    

def get_account_info(account):
    logger.info(f'Getting account info for account {account}')
    data ={
        "method": "account_info",
        "params": [
            {
                "account": account,
                "strict": True,
                "ledger_index": "current",
                "queue": True
            }
        ]
    }
    return query_ledger_api(data)


def get_account_lines(account):
    """
    retrieve account lines from xrpl api

    :param account: the adress
    :return: response
    """
    logger.info(f'Getting account lines for account {account}')
    data ={
        "method": "account_lines",
        "params": [
            {
            "account":  account
            }
        ]
    }
    return query_ledger_api(data)
    

def query_ledger_api(data):
    logger.debug(f"Payload for call is {data}")
    try:
        response = requests.post(
                RIPPLED_SERVER_URL,
                data=json.dumps(data),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
        response.encoding = 'utf-8'
        logger.debug(f'response from server {response.json()}')
        return response
    except Exception as err:
        logger.error(f'Unable to contact api: {err}')

def get_xrp_fiat_ratio(currency):
    api_url = COINSTAT_API_URL + f'coins/ripple?currency={currency}'

    try:
        logger.debug(f'calling coinstat api at {api_url}')
        response = requests.get(
                api_url,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
        response.encoding = 'utf-8'
        logger.debug(f'response from server {response.json()}')
        return float(response.json().get('coin').get('price'))
    except Exception as err:
        logger.error(f'Error when contacting coinstats api: {err}')

def get_offers_for_token(token, issuer_account):
    offer_count = 10
    data = {
        "method": "book_offers",
        "params": [
            {
                "taker_gets":{
                    "currency": "XRP"
                },
                "taker_pays": {
                    "currency": token,
                    "issuer": issuer_account
                },
                "limit": offer_count
            }
        ]
    }
    return query_ledger_api(data)

main()
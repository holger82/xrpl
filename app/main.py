import json
import logging, logging.handlers
from datetime import datetime
from typing import Optional

import requests
import statistics
import uvicorn # leave in here for requirements detection!
import secrets
from pydantic import constr, validator
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from .config import settings
from .model import Currency


app = FastAPI(
            title="XRPL Ledger Account Info API",
            description="This API assembles information from the XRP ledger and provides a json api on top of it.",
            root_path="/")

security = HTTPBasic()
logger = logging.getLogger()


def authorize(credentials: HTTPBasicCredentials = Depends(security)):
    is_user_ok = secrets.compare_digest(credentials.username, settings.API_USER_NAME)
    is_pass_ok = secrets.compare_digest(credentials.password, settings.API_USER_PASSWORD)

    if not (is_user_ok and is_pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect user or password.',
            headers={'WWW-Authenticate': 'Basic'},
        )


@app.get("/account/{account_id}")
async def account_info(account_id, currency: Optional[Currency] = settings.CURRENCY, dependencies=Depends(authorize)):
    ACCOUNT = account_id
    CURRENCY = currency
    XRP_PER_FIAT = _get_xrp_fiat_ratio(CURRENCY)

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

    account_info = _get_account_info(ACCOUNT).json()
    result['balance_xrp'] = float(account_info['result']['account_data']['Balance']) / 1000000
    
    account_lines = _get_account_lines(ACCOUNT).json()
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
        
        xrp_per_token = _get_avg_price_for_token( token, account_line['account'])
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
 
        result['balance_baselines_xrp'] = float(result['balance_baselines_xrp']) + balance_xrp
        result['balance_total'] = float(result['balance_baselines_xrp']) + float(result['balance_xrp'])
        result['balance_total_fiat'] = round(float(result['balance_total']) * XRP_PER_FIAT,2)

    #with open('out/json_result.json',"w") as f:
     #   f.write(json.dumps(result, indent=4))
    return JSONResponse(result)
        

def _get_avg_price_for_token(token, issuer_account):
    offers = _get_offers_for_token(token, issuer_account).json()
    xrp_per_token_list = []
    for offer in offers['result']['offers']:
        taker_gets = float(offer['TakerGets'])
        taker_pays = float(offer['TakerPays']['value'])
        xrp_per_token_list.append(taker_gets/taker_pays/1000000)
        logger.debug(f'Analysing offers. Curency: {token}, ratio: {taker_gets/taker_pays/1000000} | GET {taker_gets}, PAY {taker_pays}')

    return statistics.mean(xrp_per_token_list)  


def _get_server_info():
    logger.info('Getting server info for account')
    data = {
        "method": "server_info",
        "params": [
            {
                "api_version": 1
            }
        ]
    }
    return _query_ledger_api(data)
   

def _get_account_info(account):
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
    return _query_ledger_api(data)


def _get_account_lines(account):
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
    return _query_ledger_api(data)
    

def _query_ledger_api(data):
    logger.debug(f"Payload for call is {data}")
    try:
        response = requests.post(
                settings.RIPPLED_SERVER_URL,
                data=json.dumps(data),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
        response.encoding = 'utf-8'
        logger.debug(f'response from server {response.json()}')
        return response
    except Exception as err:
        logger.error(f'Unable to contact api: {err}')

def _get_xrp_fiat_ratio(currency):
    api_url = settings.COINSTAT_API_URL + f'coins/ripple?currency={currency}'

    try:
        logger.debug(f'calling coinstat api at {api_url}')
        response = requests.get(
                api_url,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
        response.encoding = 'utf-8'
        logger.debug(f'response from server {response.json()}')
        ratio = float(response.json().get('coin').get('price')) 
        logger.info(f'Calculated price for XRP to {currency} is {ratio}')

        return ratio
    except Exception as err:
        logger.error(f'Error when contacting coinstats api: {err}')

def _get_offers_for_token(token, issuer_account):
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
    return _query_ledger_api(data)
from fastapi import APIRouter
import requests
from dotenv import load_dotenv
import os

load_dotenv()

router = APIRouter()

@router.get("/")
def ping():
    return {"message": True}

# TODO: Source code, token name, symbol, top 100 holders

def get_contract_source_code(token_address):
    URL = f'''https://api.etherscan.io/api?module=contract&action=getsourcecode&address={token_address}&apikey={os.getenv('ETHERSCAN_API_KEY')}'''

    response = requests.get(URL)
    data = response.json()

    if data['status'] == "1":
        source_code = data['result'][0]['SourceCode']
        return source_code
    else:
        error_message = data['message']
        raise Exception(f"Error retrieving source code: {error_message}")


def get_token_holders(token_address):
    URL = f'''https://api.etherscan.io/api?module=token&action=tokenholderlist&contractaddress={token_address}&page=1&offset=10&apikey={os.getenv('ETHERSCAN_API_KEY')}'''

    response = requests.get(URL)
    data = response.json()

    if data['status'] == "1":
        return data['result']
    else:
        error_message = data['message']
        raise Exception(f"Error retrieving token holders: {error_message}")


def get_token_info(token_address):
    URL = f'''https://api.etherscan.io/api?module=token&action=tokeninfo&contractaddress={token_address}&apikey={os.getenv('ETHERSCAN_API_KEY')}'''

    response = requests.get(URL)

    print(response.text)
    data = response.json()

    if data['status'] == "1":
        raw_data = data['result'][0]
        keys = ['contractAddress', 'tokenName', 'symbol', 'divisor', 'tokenType', 'totalSupply', 'blueCheckmark',
                'description', 'website', 'twitter', 'telegram']
        return {key: raw_data[key] for key in keys}
    else:
        error_message = data['message']
        raise Exception(f"Error retrieving token information: {error_message}")

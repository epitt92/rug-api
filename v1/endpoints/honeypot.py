from fastapi import APIRouter
import requests
import os
import dotenv

dotenv.load_dotenv()

router = APIRouter()

@router.get("/")
def ping():
    return {"message": True}


def fetch_data(contract_address: str, pair_address: str, router_address: str, chain_id: int = 1):
    params = {
        'chainId': chain_id,
        'address': contract_address,
        'pair': pair_address,
        'router': router_address,
    }

    response = requests.get(os.getenv('HONEYPOT_IS_ENDPOINT'), params=params)

    return response.json() if response.status_code == 200 else None


@router.get("/honeypot")
def honeypot(contract_address: str, pair_address: str, router_address: str, chain_id: int):
    honeypot_check = fetch_data(contract_address, pair_address, router_address, chain_id)

    if (honeypot_check is None) or (honeypot_check.get('simulationSuccess') == False):
        return {"message": 200}
    else:
        response = honeypot_check.get('honeypotResult').get('isHoneypot')
        return {"message": response}


@router.get("/taxInfo")
def tax_info(contract_address: str, pair_address: str, router_address: str, chain_id: int):
    honeypot_check = fetch_data(contract_address, pair_address, router_address, chain_id)

    if (honeypot_check is None) or (honeypot_check.get('simulationSuccess') == False):
        return {"message": 200}
    else:
        response = honeypot_check.get('simulationResult')
        return {"message": response}


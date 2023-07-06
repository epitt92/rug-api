from fastapi import APIRouter
import os
import requests
from core.models import response, error, success

router = APIRouter()


# @router.get("/holders/{chain_id}/{token_address}")
# async def fetch_holder_list(chain_id: int, token_address: str):
#     api_key = os.getenv('ETHERSCAN_API_KEY')

#     url = 'https://api.etherscan.io/api'

#     params = {
#         'module': 'token',
#         'action': 'tokenholderlist',
#         'contractaddress': token_address,
#         'page': 1,
#         'offset': 10,
#         'apikey': api_key
#     }

#     try:
#         result = requests.get(url, params=params)
#         result.raise_for_status()
#         data = result.json()

#         if data['status'] == "1":
#             output = data['result']
#             return response(output)
#         else:
#             return error(f"An external API response error occurred with message: {data['message']}")
#     except requests.exceptions.RequestException as e:
#         return error(f"A request exception occurred with error: {e}.")

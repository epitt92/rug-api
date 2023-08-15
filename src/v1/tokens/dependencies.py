import requests, math, logging, os, dotenv

from src.v1.tokens.schemas import ContractResponse, ContractItem
from src.v1.tokens.constants import BURN_TAG, ZERO_ADDRESS, ANTI_WHALE_MAPPING, HIDDEN_OWNER_MAPPING, OPEN_SOURCE_MAPPING, HONEYPOT_MAPPING, PROXY_MAPPING, TRADING_COOLDOWN_MAPPING, CANNOT_SELL_ALL_MAPPING, OWNER_CHANGE_BALANCE_MAPPING, SELF_DESTRUCT_MAPPING, BLACKLIST_MAPPING, WHITELIST_MAPPING, HONEYPOT_SAME_CREATOR
from src.v1.shared.constants import CHAIN_ID_MAPPING
from src.v1.shared.models import ChainEnum

dotenv.load_dotenv()

simple_mapping = {
    'anti_whale_modifiable': ANTI_WHALE_MAPPING,
    'hidden_owner': HIDDEN_OWNER_MAPPING,
    'is_open_source': OPEN_SOURCE_MAPPING,
    'is_honeypot': HONEYPOT_MAPPING,
    'is_proxy': PROXY_MAPPING,
    'trading_cooldown': TRADING_COOLDOWN_MAPPING,
    'cannot_sell_all': CANNOT_SELL_ALL_MAPPING,
    'owner_change_balance': OWNER_CHANGE_BALANCE_MAPPING,
    'selfdestruct': SELF_DESTRUCT_MAPPING,
    'is_blacklisted': BLACKLIST_MAPPING,
    'is_whitelisted': WHITELIST_MAPPING,
    'honeypot_with_same_creator': HONEYPOT_SAME_CREATOR
}

def get_go_plus_data(chain: ChainEnum, token_address: str):
    _token_address = token_address.lower()

    url = f'https://api.gopluslabs.io/api/v1/token_security/{CHAIN_ID_MAPPING[chain.value]}'

    params = {
        'contract_addresses': token_address
    }

    request_response = requests.get(url, params=params)
    request_response.raise_for_status()

    data = request_response.json()['result']
    return data[_token_address]

def get_go_plus_summary(chain: ChainEnum, token_address: str):
    data = get_go_plus_data(chain, token_address)

    # Format response data into output format
    output = {}

    output['contractDeployer'] = data.get('creator_address')

    if data.get('holder_count'):
        output['holders'] = int(data['holder_count'])
    else:
        output['holders'] = None

    if data.get('buy_tax'):
        buy_tax = data.get('buy_tax')
        if isinstance(buy_tax, str):
            if len(buy_tax) > 0:
                output['buyTax'] = float(buy_tax)
            else:
                output['buyTax'] = None
        else:
            raise HTTPException(status_code=500, detail=f'Buy tax {buy_tax} is not a string')

    if data.get('sell_tax'):
        sell_tax = data.get('sell_tax')
        if isinstance(sell_tax, str):
            if len(sell_tax) > 0:
                output['sellTax'] = float(sell_tax)
            else:
                output['sellTax'] = None
        else:
            raise HTTPException(status_code=500, detail=f'Sell tax {sell_tax} is not a string')

    # Liquidity token calculations
    if data.get('dex'):
        try:
            output['liquidityUsd'] = sum([float(item['liquidity']) for item in data['dex']])
        except:
            output['liquidityUsd'] = None
    else:
        output['liquidityUsd'] = None

    # Locked and burned liquidity calculations
    if data.get('lp_holders'):
        lp_holders = data.get('lp_holders')

        lockedLiquidity, burnedLiquidity = 0.0, 0.0
        for lp in lp_holders:
            if lp.get('percent'):
                percent = float(lp.get('percent'))
                if lp.get("tag") == BURN_TAG:
                    burnedLiquidity += percent
                elif lp.get("is_locked") == 1:
                    lockedLiquidity += float(lp.get('percent'))

        output['lockedLiquidity'] = lockedLiquidity if lockedLiquidity > 0.001 else 0.0
        output['burnedLiquidity'] = burnedLiquidity if burnedLiquidity > 0.001 else 0.0
    else:
        output['lockedLiquidity'] = None
        output['burnedLiquidity'] = None

    return output


def get_block_explorer_data(chain: ChainEnum, token_address: str):
    _chain = str(chain.value) if isinstance(chain, ChainEnum) else str(chain)

    try:
        prefix = os.environ.get(f'{_chain.upper()}_BLOCK_EXPLORER_URL')
        api_key = os.environ.get(f'{_chain.upper()}_BLOCK_EXPLORER_API_KEY')
        
        params = {
                'module': 'token',
                'action': 'tokeninfo',
                'contractaddress': token_address,
                'apikey': api_key
        }

        result = requests.get(prefix, params=params)
        result.raise_for_status()
        data = result.json()['result']

        logging.warning(f'block explorer data: {data}')
        logging.warning(f'block explorer data keys: {data.keys()}')

        output = {}
        output['name'] = data['tokenName']
        output['symbol'] = data['symbol']
        output['decimals'] = int(data['divisor'])
        output['totalSupply'] = int(data['totalSupply']) / (10 ** int(data['divisor']))

        # TODO: Temporarily make circulating supply the same as total supply
        output['circulatingSupply'] = data['totalSupply']
        output['totalSupplyPercentage'] = 1.0

        output['website'] = data['website'] if data['website'] != '' else None
        output['twitter'] = data['twitter'] if data['twitter'] != '' else None
        output['telegram'] = data['telegram'] if data['telegram'] != '' else None
        output['discord'] = data['discord'] if data['discord'] != '' else None
    except Exception as e:
        logging.error(f'Error getting block explorer data: {e}')
        output = {}

    return output


def get_supply_summary(go_plus_response: dict) -> dict:
    logging.info(f'go plus response keys: {go_plus_response.keys()}')
    items = []

    simple_keys = ['hidden_owner', 'is_open_source', 'is_proxy', 'selfdestruct']

    for key in simple_keys:
        if go_plus_response.get(key):
            response = bool(int(go_plus_response.get(key)))
            items.append({'title':simple_mapping[key][response]['title'],
                            'description': simple_mapping[key][response]['description'],
                            'severity': simple_mapping[key][response]['severity']})

    # Add ownership renounced field
    if go_plus_response.get('can_take_back_ownership') and go_plus_response.get('owner_address'):
        renounced_ownership, can_recall = bool(go_plus_response.get('owner_address') == ZERO_ADDRESS), bool(int(go_plus_response.get('can_take_back_ownership')))

        if renounced_ownership and not can_recall:
            items.append({'title': 'Ownership Renounced', 'description': 'The contract owner has renounced ownership of the contract and cannot recall ownership.', 'severity': 0})
        elif renounced_ownership and can_recall:
            items.append({'title':'Ownership Renounced', 'description': 'The contract owner has renounced ownership of the contract, however our algorithms detected that the owner can recall ownership at any time, proceed with caution when interacting with this contract.', 'severity': 1})
        elif not renounced_ownership:
            items.append({'title':'Has Owner', 'description': 'The contract owner has not renounced ownership of the contract, meaning that any owner enabled functions could be utilized to modify the token.', 'severity': 2})
    else:
        logging.error(f'Could not find owner address or can_take_back_ownership in go plus response.')

    # Add mintability field
    if go_plus_response.get('is_mintable'):
        if bool(int(go_plus_response.get('is_mintable'))):
            if renounced_ownership and not can_recall:
                items.append({'title': 'Mintable', 'description': 'The contract has minting functionality, but our algorithms detected that ownership of the contract has been revoked and cannot be recalled. Proceed with caution when interacting with this token.', 'severity': 2})
            elif renounced_ownership and can_recall:
                items.append({'title': 'Mintable', 'description': 'The contract has minting functionality, but since ownership has been revoked, the owner may not be able to mint additional tokens currently. However, our algorithms detected that the owner can recall ownership at any time, proceed with caution when interacting with this contract.', 'severity': 3})
            elif not renounced_ownership:
                items.append({'title': 'Mintable', 'description': 'The contract has minting functionality, meaning that the owner could mint new tokens at any time. Since the ownership of this token is not renounced, traders should proceed with caution.', 'severity': 3})
        else:
            items.append({'title': 'Not Mintable', 'description': 'The contract does not have minting functionality.', 'severity': 0})
    else:
        logging.warning(f'No is_mintable field in go plus response: {go_plus_response}')

    additional_summary = ''
    if go_plus_response.get('selfdestruct'):
        if bool(go_plus_response.get('selfdestruct')):
            additional_summary += 'The owner could destroy the contract at any time. '
    
    if go_plus_response.get('is_mintable'):
        if bool(go_plus_response.get('is_mintable')):
            additional_summary += 'The owner could mint new tokens at any time. '

    if go_plus_response.get('is_proxy'):
        if bool(go_plus_response.get('is_proxy')):
            additional_summary += 'The contract is a proxy contract. '

    if go_plus_response.get('is_open_source'):
        if not bool(go_plus_response.get('is_open_source')):
            additional_summary += 'The contract is not open source. '

    if go_plus_response.get('hidden_owner'):
        if bool(go_plus_response.get('hidden_owner')):
            additional_summary += 'The contract owner is hidden. '

    score = calculate_score(items=items)

    summary = create_brief_summary(items=items, additional_summary=additional_summary)

    return {'items': items, 'score': score, 'summary': summary}


def get_transferrability_summary(go_plus_response: dict) -> dict:
    items = []

    simple_keys = ['anti_whale_modifiable', 'is_honeypot', 'trading_cooldown', 'cannot_sell_all', 'owner_change_balance', 'is_blacklisted', 'is_whitelisted', 'honeypot_with_same_creator']

    for key in simple_keys:
        if go_plus_response.get(key):
            response = bool(int(go_plus_response.get(key)))
            items.append({'title': simple_mapping[key][response]['title'],
                                      'description': simple_mapping[key][response]['description'],
                                      'severity': simple_mapping[key][response]['severity']})

    # Add buy tax field
    if go_plus_response.get('buy_tax'):
        buy_tax = float(go_plus_response.get('buy_tax'))
        if buy_tax > 0.1:
            items.append({'title': '{100*buy_tax:.1f}% Buy Tax', 'description': f'This token has a buy tax of {100*buy_tax:.1f}% which is very high.', 'severity': 3})
        elif buy_tax > 0.05:
            items.append({'title': '{100*buy_tax:.1f}% Buy Tax', 'description': f'This token has a buy tax of {100*buy_tax:.1f}% which is high.', 'severity': 2})
        elif buy_tax > 0.01:
            items.append({'title': '{100*buy_tax:.1f}% Buy Tax', 'description': f'This token has a buy tax of {100*buy_tax:.1f}% which is fairly low.', 'severity': 1})
        elif buy_tax > 0.001:
            items.append({'title': 'Low Buy Tax', 'description': f'This token has a buy tax of {100*buy_tax:.2f}% which is very low.', 'severity': 0})
        else:
            items.append({'title': 'No Buy Tax', 'description': 'This token does not have a buy tax.', 'severity': 0})

    # Add sell tax field
    if go_plus_response.get('sell_tax'):
        sell_tax = float(go_plus_response.get('sell_tax'))
        if sell_tax > 0.1:
            items.append({'title': '{100*sell_tax:.1f}% Sell Tax', 'description': f'This token has a sell tax of {100*sell_tax:.1f}% which is very high.', 'severity': 3})
        elif sell_tax > 0.05:
            items.append({'title': '{100*sell_tax:.1f}% Sell Tax', 'description': f'This token has a sell tax of {100*sell_tax:.1f}% which is high.', 'severity': 2})
        elif sell_tax > 0.01:
            items.append({'title': '{100*sell_tax:.1f}% Sell Tax', 'description': f'This token has a sell tax of {100*sell_tax:.1f}% which is fairly low.', 'severity': 1})
        elif sell_tax > 0.001:
            items.append({'title': 'Low Sell Tax', 'description': f'This token has a sell tax of {100*sell_tax:.2f}% which is very low.', 'severity': 0})
        else:
            items.append({'title': 'No Sell Tax', 'description': 'This token does not have a sell tax.', 'severity': 0})

    # Add transfer pausable
    if go_plus_response.get('can_take_back_ownership') and go_plus_response.get('owner_address'):
        renounced_ownership = bool(go_plus_response.get('owner_address') == ZERO_ADDRESS)
        can_recall = bool(int(go_plus_response.get('can_take_back_ownership')))

    if go_plus_response.get('transfer_pausable'):
        if bool(int(go_plus_response.get('transfer_pausable'))):
            if renounced_ownership and not can_recall:
                items.append({'title': 'Transfers Pausable', 'description': 'The contract has transfer pausing functionality, but our algorithms detected that ownership of the contract has been revoked and cannot be recalled. It is possible that this token could be vulnerable, proceed with caution when interacting with this token.', 'severity': 2})
            elif renounced_ownership and can_recall:
                items.append({'title': 'Transfers Pausable', 'description': 'The contract has transfer pausing functionality, but since ownership has been revoked, the owner may not be able to pause transfers currently. However, our algorithms detected that the owner can recall ownership at any time, proceed with caution when interacting with this contract.', 'severity': 3})
            elif not renounced_ownership:
                items.append({'title': 'Transfers Pausable', 'description': 'The contract has transfer pausing functionality, meaning that the owner could pause transfers at any time. Since the ownership of this token is not renounced, traders should proceed with caution.', 'severity': 3})
        else:
            items.append({'title': 'Transfers Not Pausable', 'description': 'The contract does not have transfer pausing functionality.', 'severity': 0})


    additional_summary = ''
    if go_plus_response.get('is_honeypot'):
        if bool(go_plus_response.get('is_honeypot')):
            additional_summary += ' This token is a honeypot.'

    if go_plus_response.get('trading_cooldown'):
        if bool(go_plus_response.get('trading_cooldown')):
            additional_summary += ' This token has a trading cooldown.'

    if go_plus_response.get('cannot_sell_all'):
        if bool(go_plus_response.get('cannot_sell_all')):
            additional_summary += ' This token has a sell cooldown.'

    if go_plus_response.get('owner_change_balance'):
        if bool(go_plus_response.get('owner_change_balance')):
            additional_summary += ' This token has a balance changing owner.'

    if go_plus_response.get('is_blacklisted'):
        if bool(go_plus_response.get('is_blacklisted')):
            additional_summary += ' This token is blacklisted.'

    if go_plus_response.get('is_whitelisted'):
        if bool(go_plus_response.get('is_whitelisted')):
            additional_summary += ' This token is whitelisted.'

    if go_plus_response.get('honeypot_with_same_creator'):
        if bool(go_plus_response.get('honeypot_with_same_creator')):
            additional_summary += ' This token has the same creator as a known honeypot.'

    score = calculate_score(items=items)
    summary = create_brief_summary(items=items, additional_summary=additional_summary)

    return {'items': items, 'score': score, 'summary': summary}


def calculate_score(items: list) -> int:
    """
    Given a list of ContractItem objects, calculate the overall score of the contract.
    We use a sigmoid function described as below:
    f(X) = 100 * ( 1 -  1/(1 + e^(SUM(xi + k)^p - h)) )
    where xi is the severity of the ith item, and k, p, and h are constants.

    Below, the description of the constants:
        k: It is a correction factor that adjusts the base value of the severity penalty.
        p: It is a factor that reduces the impact of low penalties (from 0 to 1) and increases the
            impact of high penalties (1 or larger).
        h: Threshold value that, if equal to the sum of the penalties, the score is 50.

    Args:
        items (list): List of ContractItem objects.
    Returns :
        (int): Score from 0 to 100 that represents the overall score of the contract.
    """
    # Constants
    k = 0.25
    p = 2
    h = 5

    # Calculate score
    penalty_param = sum(item['severity'] + k for item in items) ** p
    score = 100 * (1 - 1 / (1 + math.exp(penalty_param - h)))

    return int(score)


def create_brief_summary(items: list, additional_summary: str) -> str:
    """
    Given a list of ContractItem objects, create a brief summary of the contract.
    The summary is a string that contains the intro text.

    Args:
        items (list): List of ContractItem objects.
        additional_summary (str): Additional summary to be added to the end of the intro text.
    Returns:
        (str): Brief summary of the contract.
    """
    if len(items) == 0:
        # There is no concerns, give a standardized summary
        intro_summary = ('No major concerns were found with this token. '
                         'However, please note that this is not a guarantee of safety. ')
    else:
        # There are concerns, give a standardized summary
        intro_summary = ('Issues were found with this token. For further details, '
                         'please see the list of issues below. ')

    extension = 'Be aware that: ' if len(additional_summary) > 0 else ''

    full_summary = intro_summary + extension + additional_summary

    return full_summary

import requests

from src.v1.tokens.schemas import ContractResponse, ContractItem
from src.v1.tokens.constants import ZERO_ADDRESS, ANTI_WHALE_MAPPING, HIDDEN_OWNER_MAPPING, OPEN_SOURCE_MAPPING, HONEYPOT_MAPPING, PROXY_MAPPING, TRADING_COOLDOWN_MAPPING, CANNOT_SELL_ALL_MAPPING, OWNER_CHANGE_BALANCE_MAPPING, SELF_DESTRUCT_MAPPING, BLACKLIST_MAPPING, WHITELIST_MAPPING, HONEYPOT_SAME_CREATOR
from src.v1.shared.constants import CHAIN_ID_MAPPING
from src.v1.shared.models import ChainEnum

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

def get_go_plus_summary(chain: ChainEnum, token_address: str):
    url = f'https://api.gopluslabs.io/api/v1/token_security/{CHAIN_ID_MAPPING[chain.value]}'

    params = {
        'contract_addresses': token_address
    }

    request_response = requests.get(url, params=params)
    request_response.raise_for_status()
    return request_response.json()


def get_supply_summary(go_plus_response: dict) -> dict:
    items = []

    simple_keys = ['hidden_owner', 'is_open_source', 'is_proxy', 'selfdestruct']

    for key in simple_keys:
        if go_plus_response.get(key):
            response = bool(int(go_plus_response.get(key)))
            items.append({'title':simple_mapping[key][response]['title'], 
                            'description': simple_mapping[key][response]['description'], 
                            'severity': simple_mapping[key][response]['severity']})

    # Add ownership renounced field
    renounced_ownership, can_recall = bool(go_plus_response.get('owner_address') == ZERO_ADDRESS), bool(int(go_plus_response.get('can_take_back_ownership')))

    if renounced_ownership and not can_recall:
        items.append({'title': 'Ownership Renounced', 'description': 'The contract owner has renounced ownership of the contract and cannot recall ownership.', 'severity': 0})
    elif renounced_ownership and can_recall:
        items.append({'title':'Ownership Renounced', 'description': 'The contract owner has renounced ownership of the contract, however our algorithms detected that the owner can recall ownership at any time, proceed with caution when interacting with this contract.', 'severity': 1})
    elif not renounced_ownership:
        items.append({'title':'Has Owner', 'description': 'The contract owner has not renounced ownership of the contract, meaning that any owner enabled functions could be utilized to modify the token.', 'severity': 2})

    # Add mintability field
    if bool(int(go_plus_response.get('is_mintable'))):
        if renounced_ownership and not can_recall:
            items.append({'title': 'Mintable', 'description': 'The contract has minting functionality, but our algorithms detected that ownership of the contract has been revoked and cannot be recalled. Proceed with caution when interacting with this token.', 'severity': 2})
        elif renounced_ownership and can_recall:
            items.append({'title': 'Mintable', 'description': 'The contract has minting functionality, but since ownership has been revoked, the owner may not be able to mint additional tokens currently. However, our algorithms detected that the owner can recall ownership at any time, proceed with caution when interacting with this contract.', 'severity': 3})
        elif not renounced_ownership:
            items.append({'title': 'Mintable', 'description': 'The contract has minting functionality, meaning that the owner could mint new tokens at any time. Since the ownership of this token is not renounced, traders should proceed with caution.', 'severity': 3})
    else:
        items.append({'title': 'Not Mintable', 'description': 'The contract does not have minting functionality.', 'severity': 0})

    score = 100

    # Run manual checks to determine score
    if bool(go_plus_response.get('selfdestruct')):
        score = max(min(score - 20, 50), 0)
    if bool(go_plus_response.get('is_mintable')):
        score = max(min(score - 50, 5), 0)
    if bool(go_plus_response.get('is_proxy')):
        score = max(min(score - 5, 70), 0)
    if not bool(go_plus_response.get('is_open_source')):
        score = max(min(score - 5, 70), 0)
    if bool(go_plus_response.get('hidden_owner')):
        score = max(min(score - 40, 70), 0)

    return {'items': items, 'score': score}


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
    renounced_ownership = bool(go_plus_response.get('owner_address') == ZERO_ADDRESS)
    can_recall = bool(int(go_plus_response.get('can_take_back_ownership')))

    if bool(int(go_plus_response.get('transfer_pausable'))):
        if renounced_ownership and not can_recall:
            items.append({'title': 'Transfers Pausable', 'description': 'The contract has transfer pausing functionality, but our algorithms detected that ownership of the contract has been revoked and cannot be recalled. It is possible that this token could be vulnerable, proceed with caution when interacting with this token.', 'severity': 2})
        elif renounced_ownership and can_recall:
            items.append({'title': 'Transfers Pausable', 'description': 'The contract has transfer pausing functionality, but since ownership has been revoked, the owner may not be able to pause transfers currently. However, our algorithms detected that the owner can recall ownership at any time, proceed with caution when interacting with this contract.', 'severity': 3})
        elif not renounced_ownership:
            items.append({'title': 'Transfers Pausable', 'description': 'The contract has transfer pausing functionality, meaning that the owner could pause transfers at any time. Since the ownership of this token is not renounced, traders should proceed with caution.', 'severity': 3})
    else:
        items.append({'title': 'Transfers Not Pausable', 'description': 'The contract does not have transfer pausing functionality.', 'severity': 0})

    score = 100

    # Run manual checks to determine score
    if bool(go_plus_response.get('is_honeypot')):
        score = max(min(score, 0), 0)
    if bool(go_plus_response.get('trading_cooldown')):
        score = max(min(score - 10, 80), 0)
    if bool(go_plus_response.get('cannot_sell_all')):
        score = max(min(score - 15, 80), 0)
    if bool(go_plus_response.get('owner_change_balance')):
        score = max(min(score - 50, 25), 0)
    if bool(go_plus_response.get('is_blacklisted')):
        score = max(min(score - 10, 80), 0)
    if bool(go_plus_response.get('is_whitelisted')):
        score = max(min(score - 30, 80), 0)
    if bool(go_plus_response.get('honeypot_with_same_creator')):
        score = max(min(score, 0), 0)

    return {'items': items, 'score': score}

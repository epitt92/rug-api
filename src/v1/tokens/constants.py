import random

from src.v1.tokens.schemas import Holder, Cluster, ClusterResponse, AIComment

BURN_TAG = "Null Address"
ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'

##########################################################
#                                                        #
#              Supply Section Constants                  #
#                                                        #
##########################################################

SCORE_BASELINE = -5.0

ANTI_WHALE_MAPPING = {
    True: {'title': 'Has Anti-Whale Functionality',
          'description': "The token has anti-whale functionality, which restricts the amount of tokens a single address can hold or trade. This mechanism prevents single addresses from acquiring large percentages of supply, but traders should review the [rug.ai](https://rug.ai) Liquidity Report to ensure that there are no clusters of connected addresses present.",
          'severity': 0},
    False: {'title': "Does Not Have Anti-Whale Functionality",
           'description': "The token does not have anti-whale functionality, meaning there are no restrictions imposed on the amount of tokens a single address can hold or trade. Traders should review the [rug.ai](https://rug.ai) Liquidity Report for more information on the holder distribution for this token.",
           'severity': 0}
}

HIDDEN_OWNER_MAPPING = {
    True: {'title': 'Has Hidden Owner',
          'description': "The contract has a hidden owner, making it difficult to identify the true owner. This may mean that the hidden owner has access to malicious functionality on this token contract.",
          'severity': 3},
    False: {'title': "Does Not Have Hidden Owner",
           'description': "The contract does not have a hidden owner, meaning the identity of the contract owner is known and transparent.",
           'severity': 0}
}

OPEN_SOURCE_MAPPING = {
    True: {'title': 'Open Source',
            'description': "The contract is open source, meaning its code is publicly available, allowing for our algorithms to analyze the contract for vulnerabilities.",
            'severity': 0},
    False: {'title': "Not Open Source",
           'description': "The contract is not open source, meaning its code is not publicly available. This means that our algorithms are unable to audit the token smart contract and detect vulnerabilities, please proceed with caution when interacting with this token.",
           'severity': 2}
}

PROXY_MAPPING = {
    True: {'title': 'Proxy Contract',
            'description': "The contract is a proxy contract, meaning it delegates calls to another contract called an implementation contract. A contract which does make delegate calls to other contracts may risk having its implementation change over time, which could introduce additional risks for traders of the token.",
            'severity': 1},
    False: {'title': "Not Proxy Contract",
           'description': "The contract is not a proxy contract, meaning it does not make delegate calls to other contracts. A contract which does make delegate calls to other contracts may risk having its implementation change over time, which could introduce additional risks for traders of the token.",
            'severity': 0}
}

OWNER_CHANGE_BALANCE_MAPPING = {
    True: {'title': 'Owner Can Change Balance',
           'description': "The owner of this token can modify the balance of holders of this token, potentially stealing funds from traders.",
           'severity': 10},
    False: {'title': "Owner Cannot Change Balance",
           'description': "This token does not enable an owner from modifying the balance of holders, which is sometimes used as a tactic by other tokens to steal funds from traders.",
            'severity': 0}
}

SELF_DESTRUCT_MAPPING = {
    True: {'title': 'Contract Has Self Destruct OP Code',
           'description': "The contract has a self-destruct OP code, giving the owner the ability to permanently destroy the contract. This action renders any associated tokens useless and results in a total loss for token holders.",
           'severity': 50},
    False: {'title': "No Self Destruct OP Code",
           'description': "The contract does not have a self-destruct OP code, ensuring that the contract cannot be permanently destroyed by the owner.",
            'severity': 0}
}

##########################################################
#                                                        #
#         Transferrability Section Constants             #
#                                                        #
##########################################################

HONEYPOT_MAPPING = {
    True: {'title': 'Honeypot Contract',
            'description': "This token is a honeypot, meaning that the token traps users' funds. Avoid trading this token, doing so may mean losing your entire investment.",
           'severity': 100},
    False: {'title': "Not Honeypot Contract",
           'description': "The token is not a honeypot, indicating that it does not employ deceptive tactics to trap users' funds.",
            'severity': 0}
}

TRADING_COOLDOWN_MAPPING = {
    True: {'title': 'Trading Cooldown',
            'description':  "The token has a trading cooldown, which requires a certain amount of time to pass between trades. This mechanism can be employed to prevent manipulation, but it may also limit the token's liquidity and usability.",
           'severity': 1},
    False: {'title': "No Trading Cooldown",
           'description': "The token does not have a trading cooldown, allowing trades to occur without any specific time restrictions.",
            'severity': 0}
}

CANNOT_SELL_ALL_MAPPING = {
    True: {'title': 'Cannot Sell All',
           'description': "Traders cannot sell all tokens in a single transaction. This typically means that traders will have to leave a percentage of tokens in their wallet during each sale.",
           'severity': 1},
    False: {'title': "Can Sell All",
           'description': "Traders are able to liquidate all tokens in a single transaction.",
            'severity': 0}
}

BLACKLIST_MAPPING = {
    True: {'title': 'Blacklist',
           'description': "The token has blacklist functionality, allowing the owner to prevent specific addresses from buying or selling the token. However, this capability can be potentially misused for censorship or manipulation.",
           'severity': 1},
    False: {'title': "No Blacklist",
           'description': "The token does not have blacklist functionality, meaning there are no restrictions imposed by the token's owner on specific addresses regarding buying or selling the token.",
            'severity': 0}
}

WHITELIST_MAPPING = {
    True: {'title': 'Whitelist',
           'description': "The token has whitelist functionality, which means only approved addresses can interact with the token. This capability restricts the token's accessibility and use to a specific set of addresses.",
           'severity': 1},
    False: {'title': "No Whitelist",
           'description': "The token does not have whitelist functionality, meaning there are no restrictions imposed by the token on which addresses can interact with it.",
            'severity': 0}
}

HONEYPOT_SAME_CREATOR = {
    True: {'title': 'Known Scammer',
           'description': "The deployer of this token contract has previously deployed a honeypot contract, indicating that this token is likely to also be a scam. Proceed with caution when interacting with this token.",
           'severity': 3},
    False: {'title': "No Previous Honeypots",
           'description': "The deployer of this token contract does not have a history of deploying honeypot contracts.",
            'severity': 0}
}

##########################################################
#                                                        #
#            DynamoDB Staleness Constants                #
#                                                        #
##########################################################

TOKEN_METRICS_STALENESS_THRESHOLD = 60 * 30 # 30 minutes
SUPPLY_REPORT_STALENESS_THRESHOLD = 60 * 60 * 1 # 1 hour
TRANSFERRABILITY_REPORT_STALENESS_THRESHOLD = 60 * 60 * 1 # 1 hour

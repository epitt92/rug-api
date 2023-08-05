import random

from src.v1.tokens.schemas import Holder, Cluster, ClusterResponse, AIComment

##########################################################
#                                                        #
#                    AI Constants                        #
#                                                        #
##########################################################

AI_SUMMARY_DESCRIPTION = '''rug.ai AI-tooling identified **7** potential vulnerabilities in this contract which could cause partial or complete loss of funds. Therefore, we recommend proceeding with caution when interacting with this contract. In Line 7, there is also a `TransferOwnership` function which allows the ownership of the contract to be transferred to a malicious owner.'''

AI_COMMENT_1 = AIComment(commentType='Function',
                        title='_transfer',
                        description='This contract has a `_transfer` function which allows the ownership of the contract to be transferred to a malicious owner.', 
                        severity=3,
                        fileName='Token.sol',
                        sourceCode='function _transfer(address sender, address recipient, uint256 amount) internal virtual {')

AI_COMMENT_2 = AIComment(commentType='Function',
                        title='setSellFee',
                        description='This contract has a `setSellFee` function which allows the owner of the contract to modify sell fees',
                        severity=2,
                        fileName='Token.sol',
                        sourceCode='function setSellFee(uint256 _sellFee) external onlyOwner {')

AI_COMMENT_3 = AIComment(commentType='Function',
                        title='TransferOwnership',
                        description='This contract has a `TransferOwnership` function which allows the ownership of the contract to be transferred to a malicious owner.',
                        severity=1,
                        fileName='Token.sol',
                        sourceCode='function TransferOwnership(address newOwner) public onlyOwner {')

AI_COMMENT_4 = AIComment(commentType='Function',
                        title='Execute',
                        description='This contract has a `Execute` function which allows the owner of the contract to modify the balances of holders.',
                        severity=4,
                        fileName='Token.sol',
                        sourceCode='function Execute(address _from, address _to, uint256 _amount) public onlyOwner {')

AI_COMMENTS = [AI_COMMENT_1, AI_COMMENT_2, AI_COMMENT_3, AI_COMMENT_4]

AI_SCORE = 43.5

##########################################################
#                                                        #
#               Holder Chart Constants                   #
#                                                        #
##########################################################

L, R = 10, 4000

HOLDER_1 = Holder(address='0x3f2D4708F75DE6Fb60B687fEd326697634774dEb', numTokens=random.randrange(L, R), percentage=0.122)

CLUSTER_1 = Cluster(members=[Holder(address='0x3f2D4708F75DE6Fb60B687fEd326697634774dEb', numTokens=random.randrange(L, R), percentage=0.122)])

CLUSTER_2 = Cluster(members=[Holder(address='0x3f2D4708F75DE6Fb60B687fEd326697634774dEb', numTokens=random.randrange(L, R), percentage=0.043), 
                             Holder(address='0x3f2D4708F75DE6Fb60B687fEd326697634774dEb', numTokens=random.randrange(L, R), percentage=0.0023)])

CLUSTER_3 = Cluster(members=[Holder(address='0x3f2D4708F75DE6Fb60B687fEd326697634774dEb', numTokens=random.randrange(L, R), percentage=0.018)])

CLUSTER_4 = Cluster(containsDeployer=True,
                    members=[Holder(address='0x3f2D4708F75DE6Fb60B687fEd326697634774dEb', numTokens=random.randrange(L, R), percentage=0.034), 
                             Holder(address='0x3f2D4708F75DE6Fb60B687fEd326697634774dEb', numTokens=random.randrange(L, R), percentage=0.0023),
                             Holder(address='0x3f2D4708F75DE6Fb60B687fEd326697634774dEb', numTokens=random.randrange(L, R), percentage=0.0023)])

CLUSTER_5 = Cluster(members=[Holder(address='0x3f2D4708F75DE6Fb60B687fEd326697634774dEb', numTokens=random.randrange(L, R), percentage=0.002)])

CLUSTER_RESPONSE = ClusterResponse(clusters=[CLUSTER_1, CLUSTER_2, CLUSTER_3, CLUSTER_4, CLUSTER_5])

BURN_TAG = "Null Address"
ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'

##########################################################
#                                                        #
#              Supply Section Constants                  #
#                                                        #
##########################################################

ANTI_WHALE_MAPPING = {
    True: {'title': 'Has Anti-Whale Functionality',
          'description': "The token has anti-whale functionality, which restricts the amount of tokens a single address can hold or trade. This mechanism prevents single addresses from acquiring large percentages of supply, but traders should review the [rug.ai](https://rug.ai) Liquidity Report to ensure that there are no clusters of connected addresses present.",
          'severity': 0},
    False: {'title': "Does Not Have Anti-Whale Functionality",
           'description': "The token does not have anti-whale functionality, meaning there are no restrictions imposed on the amount of tokens a single address can hold or trade. Traders should review the [rug.ai](https://rug.ai) Liquidity Report for more information on the holder distribution for this token.",
           'severity': 1}
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
            'description': "The contract is open source, meaning its code is publicly available, allowing for [rug.ai](https://rug.ai) algorithms to analyze the contract for vulnerabilities.",
            'severity': 0},
    False: {'title': "Not Open Source",
           'description': "The contract is not open source, meaning its code is not publicly available. This means that [rug.ai](https://rug.ai) is unable to audit the token smart contract and detect vulnerabilities, please proceed with caution when interacting with this token.",
           'severity': 1}
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
           'severity': 3},
    False: {'title': "Owner Cannot Change Balance",
           'description': "This token does not enable an owner from modifying the balance of holders, which is sometimes used as a tactic by other tokens to steal funds from traders.",
            'severity': 0}
}

SELF_DESTRUCT_MAPPING = {
    True: {'title': 'Self Destruct',
           'description': "The contract has a self-destruct OP code, giving the owner the ability to permanently destroy the contract. This action renders any associated tokens useless and results in a total loss for token holders.",
           'severity': 3},
    False: {'title': "No Self Destruct",
           'description': "The contract does not have a self-destruct OP code, ensuring that the contract cannot be permanently destroyed by the owner.",
            'severity': 0}
}

##########################################################
#                                                        #
#         Transferrability Section Constants             #
#                                                        #
##########################################################

HONEYPOT_MAPPING = {
    True: {'title': 'Honeypot',
            'description': "This token is a honeypot, meaning that the token traps users' funds. Avoid trading this token, doing so may mean losing your entire investment.",
           'severity': 3},
    False: {'title': "Not Honeypot",
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
           'severity': 2},
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

TOKEN_METRICS_STALENESS_THRESHOLD = 60 * 5 # 5 minutes
SUPPLY_REPORT_STALENESS_THRESHOLD = 60 * 60 * 1 # 1 hour
TRANSFERRABILITY_REPORT_STALENESS_THRESHOLD = 60 * 60 * 1 # 1 hour

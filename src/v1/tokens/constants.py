import random

from src.v1.tokens.schemas import Holder, Cluster, ClusterResponse, AIComment

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

L, R = 10, 4000

HOLDER_1 = Holder(address='0x3f2D4708F75DE6Fb60B687fEd326697634774dEb', numTokens=random.randrange(L, R), percentage=0.122)

CLUSTER_1 = Cluster(members=[Holder(address='0x3f2D4708F75DE6Fb60B687fEd326697634774dEb', numTokens=random.randrange(L, R), percentage=0.122)])

CLUSTER_2 = Cluster(members=[Holder(address='0x3f2D4708F75DE6Fb60B687fEd326697634774dEb', numTokens=random.randrange(L, R), percentage=0.043), 
                             Holder(address='0x3f2D4708F75DE6Fb60B687fEd326697634774dEb', numTokens=random.randrange(L, R), percentage=0.0023)])

CLUSTER_3 = Cluster(members=[Holder(address='0x3f2D4708F75DE6Fb60B687fEd326697634774dEb', numTokens=random.randrange(L, R), percentage=0.018)])

CLUSTER_4 = Cluster(members=[Holder(address='0x3f2D4708F75DE6Fb60B687fEd326697634774dEb', numTokens=random.randrange(L, R), percentage=0.034), 
                             Holder(address='0x3f2D4708F75DE6Fb60B687fEd326697634774dEb', numTokens=random.randrange(L, R), percentage=0.0023),
                             Holder(address='0x3f2D4708F75DE6Fb60B687fEd326697634774dEb', numTokens=random.randrange(L, R), percentage=0.0023)])

CLUSTER_5 = Cluster(members=[Holder(address='0x3f2D4708F75DE6Fb60B687fEd326697634774dEb', numTokens=random.randrange(L, R), percentage=0.002)])

CLUSTER_RESPONSE = ClusterResponse(clusters=[CLUSTER_1, CLUSTER_2, CLUSTER_3, CLUSTER_4, CLUSTER_5])

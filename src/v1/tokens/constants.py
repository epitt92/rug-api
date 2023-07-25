import random

from src.v1.tokens.schemas import Holder, Cluster, ClusterResponse

AI_SUMMARY_DESCRIPTION = '''
        rug.ai AI-tooling identified **7** potential vulnerabilities in this contract which could cause partial or complete loss of funds. Therefore, we recommend proceeding with caution when interacting with this contract.

        In Line 7, there is also a `TransferOwnership` function which allows the ownership of the contract to be transferred to a malicious owner.
        '''

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

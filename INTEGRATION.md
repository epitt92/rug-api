### Instructions for Integrating Endpoints into Front End

##### Metrics

Fetched by quering the endpoint at:

```https://rug.diffusion.io/v1/tokens/info/ethereum/0x3f2D4708F75DE6Fb60B687fEd326697634774dEb```

This returns a response, for which the key `tokenSummary` can be queried, the relevant response fields are as follows:

```
"tokenSummary": {
    "lockedLiquidity": 0.9569872852270381,
    "burnedLiquidity": null,
    "buyTax": 0.07,
    "sellTax": 0.0736,
    "liquidityUsd": 47905.74258651455,
    "liquiditySingleSided": null,
    "volume24h": 23217.91156311268,
    "circulatingSupply": 10000000,
    "totalSupply": 10000000,
    "totalSupplyPercentage": 1,
    "txCount": null,
    "holders": 1042,
    "latestPrice": 0.0395214686166235
  }
```

##### lockedLiquidity

- If `lockedLiquidity` is `null`, this should be rendered as "None" on the UI, in this style:

<img width="109" alt="image" src="https://github.com/diffusion-io/rug-api/assets/99917971/6044a4c8-b79c-4f0b-89ee-61096cb7942d">

If it is not `null`, it will be a percentage value between 0% and 100%, and should be rendered on the UI, in this style:

<img width="91" alt="image" src="https://github.com/diffusion-io/rug-api/assets/99917971/5b270e03-f055-43e6-91a2-318977c995a9">

The logic for determining which colour is as follows:

- If `lockedLiquidity` >= 50%, then green
- Otherwise, then grey

##### burnedLiquidity

- If `burnedLiquidity` is `null`, this should be rendered as "None" on the UI, in this style:

<img width="109" alt="image" src="https://github.com/diffusion-io/rug-api/assets/99917971/6044a4c8-b79c-4f0b-89ee-61096cb7942d">

If it is not `null`, it will be a percentage value between 0% and 100%, and should be rendered on the UI, in this style:

<img width="91" alt="image" src="https://github.com/diffusion-io/rug-api/assets/99917971/5b270e03-f055-43e6-91a2-318977c995a9">

The logic for determining which colour is as follows:

- If `burnedLiquidity` >= 50%, then green
- Otherwise, then grey

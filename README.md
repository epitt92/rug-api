# rug-api

- Ensure Python is installed on your machine, pull the repository and open it in terminal

- Call `pip install -r requirements.txt` to install package requirements

- Add a `.env` file in the root folder with `ETHERSCAN_API_KEY = 'YOUR-API-KEY'`

- Call `uvicorn server:app --reload` to run the API locally on port `8000`

- Navigate to `localhost:8000/endpoints` in browser to view the endpoints, or `localhost:8000/documentation` to view the documentation for the API

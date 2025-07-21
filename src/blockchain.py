import requests
from type_defs import Transaction
from typing import List
from datetime import datetime

class HSKIndexer:
    def __init__(self, api_url: str = "https://hashkey.blockscout.com/api"):
        # self.contract_address = contract_address.lower()
        self.api_url = api_url

    def get_latest_block(self) -> int:
        """Get latest block number"""
        response = requests.get(self.api_url, params={
            "module": "block",
            "action": "eth_block_number"
        })
        return int(response.json()["result"], 0)

    def get_transactions(self, contract_address: str, start_block: int, end_block: int) -> List[Transaction]:
        """
        Get all successful transactions involving this contract 
        from start_block to end_block (inclusive).
        """
        contract_address = contract_address.lower()
        # get regular transactions
        response = requests.get(self.api_url, params={
            "module": "account",
            "action": "txlist",
            "address": contract_address,
            "startblock": start_block,
            "endblock": end_block,
            "sort": "asc"
        })

        data = response.json().get("result", [])

        # # get internal transactions
        # response = requests.get(self.api_url, params={
        #     "module": "account",
        #     "action": "txlistinternal",
        #     "address": self.contract_address,
        #     "startblock": start_block,
        #     "endblock": end_block,
        #     "sort": "asc"
        # })

        # # filter out internals from the same transaction
        # internal_data = response.json().get("result", [])
        # internal_data = list({tx["transactionHash"]: tx for tx in internal_data}.values())

        # data += internal_data

        return [
            {
                "block_number": tx["blockNumber"],
                "contract_address": contract_address,
                "caller_address": tx["from"],
                "tx_hash": tx.get("hash", tx.get("transactionHash")),
                "value": tx["value"],
                "timestamp": datetime.fromtimestamp(int(tx["timeStamp"])).isoformat()
            }
            for tx in data
            if tx["isError"] == "0"
            and (tx["to"] == contract_address or tx["contractAddress"] == contract_address)
            and tx.get("value") != "0" # filter out zero value transactions, such as grantRole or revokeRole
        ]

    def get_token_price_usd(self) -> float:
        """Get current price of token in USD"""
        response = requests.get(self.api_url, params={
            "module": "stats",
            "action": "ethprice"
        })
        return float(response.json()["result"]["ethusd"])

    # def compute_metrics(self, calls: list[dict]) -> dict:
    #     call_count = len(calls)
    #     unique_users = {tx["from"] for tx in calls}
    #     total_wei = sum(int(tx["value"]) for tx in calls)
    #     price_usd = self.get_eth_price_usd()
    #     total_usd = total_wei / 1e18 * price_usd

    #     return {
    #         "call_count": call_count,
    #         "unique_users": len(unique_users),
    #         "total_usd": total_usd
    #     }

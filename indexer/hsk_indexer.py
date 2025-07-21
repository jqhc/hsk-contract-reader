import requests
from types.t import Transaction
from typing import List
from datetime import datetime

class ContractMetricsMonitor:
    def __init__(self, contract_address: str, last_block: int, api_url: str = "https://mainnet.hsk.xyz/api"):
        self.contract_address = contract_address.lower()
        self.last_block = last_block
        self.api_url = api_url

    def get_latest_block(self) -> int:
        """Get latest block number"""
        response = requests.get(self.api_url, params={
            "module": "block",
            "action": "eth_block_number"
        })
        return int(response.json()["result"], 0)

    def get_transactions(self, start_block: int, end_block: int) -> List[Transaction]:
        """
        Get all successful transactions involving this contract 
        from start_block to end_block (inclusive).
        """
        response = requests.get(self.api_url, params={
            "module": "account",
            "action": "txlist",
            "address": self.contract_address,
            "startblock": start_block,
            "endblock": end_block,
            "sort": "asc"
        })

        data = response.json().get("result", [])

        response = requests.get(self.api_url, params={
            "module": "account",
            "action": "txlistinternal",
            "address": self.contract_address,
            "startblock": start_block,
            "endblock": end_block,
            "sort": "asc"
        })

        data.append(response.json().get("result", []))

        return [
            {
                "block_number": tx["blockNumber"],
                "contract_address": tx["contractAddress"],
                "from_": tx["from"],
                "to": tx["to"],
                "tx_hash": tx["hash"],
                "value": tx["value"],
                "timestamp": datetime.fromtimestamp(int(tx["timeStamp"])).isoformat()
            }
            for tx in data
            if tx.get("isError") == "0"
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

    # def poll(self):
    #     latest_block = self.get_latest_block()

    #     txs = self.fetch_transactions(self.last_block + 1, latest_block)
    #     calls = self.filter_successful_calls(txs)
    #     metrics = self.compute_metrics(calls)

    #     # Replace with actual database storage logic
    #     print(f"Metrics from block {self.last_block + 1} to {latest_block}:", metrics)

    #     self.last_block = latest_block


# Example usage:
# monitor = ContractMetricsMonitor("0xYourContractAddress")
# monitor.poll()

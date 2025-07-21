from typing import TypedDict
from datetime import datetime

class Transaction(TypedDict):
    block_number: str
    contract_address: str
    from_: str
    to: str
    tx_hash: str
    value: str
    timestamp: datetime

class ContractCall(TypedDict):
    contract_address: str
    caller_address: str
    timestamp: datetime
    amount: str
    tx_hash: str
    block_height: int

# class ContractMetrics(TypedDict):
#     contract_address: str
#     call_count: int
#     total_amount: str # store as string for precision
#     call_chains: int
#     user_count: int


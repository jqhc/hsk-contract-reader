from typing import TypedDict
from datetime import datetime

class Transaction(TypedDict):
    block_number: str
    contract_address: str
    caller_address: str
    tx_hash: str
    value: str
    timestamp: datetime

class ContractMetrics(TypedDict):
    contract_address: str
    call_count: int
    total_amount: float
    call_chains: int


from blockchain import HSKIndexer
from database import DB

# Note: it's not the Poller's job to close the DB connection (db.close()), 
# should be done by caller
# also, db should be the same one used by API to avoid race conditions
class Poller:
    def __init__(self, db: DB, indexer: HSKIndexer, 
                 contract_addresses: list[str], polling_interval: int):
        self.db = db
        self.indexer = indexer
        self.contract_addresses = contract_addresses
        # add contract to contract_states table (stores last processed block heights)
        # if not already present
        for contract in contract_addresses:
            if not db.get_last_height(contract):
                db.set_last_height(contract, 1)
        self.polling_interval = polling_interval
    
    def poll(self):
        """Polls blockchain for new transactions and updates database"""
        print("polling...")
        # locks the latest block number
        curr_block_height = self.indexer.get_latest_block()
        for contract in self.contract_addresses:
            print(f"processing contract {contract}")
            # for each contract:
            # get last processed block number for that contract
            last_block_height = self.db.get_last_height(contract)
            print(f"last block height: {last_block_height}")
            if last_block_height + 1 >= curr_block_height:
                print("No new blocks since last poll!")
                continue
            
            # gets all transactions since last poll and adds to database
            transactions = self.indexer.get_transactions(contract, last_block_height + 1, curr_block_height)
            print(f"found {len(transactions)} new transactions!")
            print([tx["tx_hash"] for tx in transactions])
            self.db.insert_contract_calls(transactions) # database automatically updates metrics
            print("inserted transactions into database")

            # updates this contract's last processed block number
            self.db.set_last_height(contract, curr_block_height)
            print(f"set last height to {curr_block_height}")


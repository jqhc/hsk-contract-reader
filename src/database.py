import sqlite3
from typing import Optional, List, Tuple
from type_defs import Transaction, ContractMetrics
import threading

class DB:
    def __init__(self, schema_file: str = "./schema.sql", db_path: str = "./hsk_data.db"):
        """Initializes the database connection and sets up the schema."""
        self.db_path = db_path
        self.mutex = threading.Lock()
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        with open(schema_file, "r") as f:
            self.conn.executescript(f.read())
        self.conn.commit()

        self.conn.row_factory = sqlite3.Row

    def close(self):
        """Closes the database connection."""
        self.conn.close()

    def insert_contract_call(self, tx: Transaction):
        """Inserts a new contract call into the database and updates metrics."""
        with self.mutex:
            self.conn.execute("""
                INSERT INTO contract_calls
                (tx_hash, block_height, contract_address, caller_address, amount, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                tx["tx_hash"],
                tx["block_number"],
                tx["contract_address"],
                tx["caller_address"],
                tx["value"],
                tx["timestamp"]
            ))

            # Update metrics
            self.conn.execute("""
                INSERT INTO contract_metrics (contract_address, call_count, total_amount, call_chains)
                VALUES (?, 1, ?, 1)
                ON CONFLICT(contract_address) DO UPDATE SET
                    call_count = call_count + 1,
                    total_amount = total_amount + excluded.total_amount
            """, (
                tx["contract_address"],
                tx["value"]
            ))

            self.conn.commit()

    def insert_contract_calls(self, txs: List[Transaction]):
        """Inserts multiple contract calls into database and updates metrics."""
        if not txs:
            return

        with self.mutex:
            self.conn.executemany("""
                INSERT INTO contract_calls
                (tx_hash, block_height, contract_address, caller_address, amount, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, [(
                    tx["tx_hash"],
                    tx["block_number"],
                    tx["contract_address"],
                    tx["caller_address"],
                    tx["value"],
                    tx["timestamp"]
                )
                for tx in txs
            ])

            # Aggregate metrics per contract
            metrics_updates = {}
            for tx in txs:
                addr = tx["contract_address"]
                metrics_updates.setdefault(addr, {"call_count": 0, "total_amount": 0.0})
                metrics_updates[addr]["call_count"] += 1
                metrics_updates[addr]["total_amount"] += float(tx["value"])

            # Insert per contract
            for contract_address, metrics in metrics_updates.items():
                self.conn.execute("""
                    INSERT INTO contract_metrics (contract_address, call_count, total_amount, call_chains)
                    VALUES (?, ?, ?, 1)
                    ON CONFLICT(contract_address) DO UPDATE SET
                        call_count = call_count + excluded.call_count,
                        total_amount = total_amount + excluded.total_amount
                """, (
                    contract_address,
                    metrics["call_count"],
                    metrics["total_amount"]
                ))

            self.conn.commit()

    def get_last_height(self, contract_address: str) -> Optional[int]:
        """Retrieves the last processed block height for a given contract address."""

        with self.mutex:
            cur = self.conn.execute("""
                SELECT last_processed_height FROM contract_states
                WHERE contract_address = ?
            """, (contract_address,))
            row = cur.fetchone()
        return row[0] if row else None

    def set_last_height(self, contract_address: str, block_height: int):
        """Updates the last processed block height for a given contract address."""

        with self.mutex:
            self.conn.execute("""
                INSERT INTO contract_states (contract_address, last_processed_height)
                VALUES (?, ?)
                ON CONFLICT(contract_address) DO UPDATE SET last_processed_height = excluded.last_processed_height
            """, (contract_address, block_height))
            self.conn.commit()

    # def update_contract_metrics(self,
    #     contract_address: str,
    #     call_count: int,
    #     total_amount: float,
    #     call_chains: int = 1
    # ):
    #     """Updates contract metrics in the database."""

    #     with self.mutex:
    #         self.conn.execute("""
    #             INSERT INTO contract_metrics
    #             (contract_address, call_count, total_amount, call_chains)
    #             VALUES (?, ?, ?, ?)
    #             ON CONFLICT(contract_address) DO UPDATE SET
    #                 call_count = excluded.call_count,
    #                 total_amount = excluded.total_amount,
    #                 call_chains = excluded.call_chains
    #         """, (
    #             contract_address,
    #             call_count,
    #             total_amount,
    #             call_chains
    #         ))
    #         self.conn.commit()

    def get_metrics_for_contract(self, contract_address: str) -> Tuple[Optional[ContractMetrics], int]:
        """
        Retrieves metrics for a specific contract from the database.
        Returns a tuple: (ContractMetrics for that contract, number of unique users for that contract)
        If the contract has no data, returns (None, 0).
        """

        with self.mutex:
            # Get contract metrics
            cur = self.conn.execute("""
                SELECT contract_address, call_count, total_amount, call_chains
                FROM contract_metrics
                WHERE contract_address = ?
            """, (contract_address,))
            row = cur.fetchone()

            if not row:
                return None, 0

            metrics = {
                "contract_address": contract_address,
                "call_count": row[1],
                "total_amount": row[2],
                "call_chains": row[3]
            }

            # Get number of unique users for this contract
            cur = self.conn.execute("""
                SELECT COUNT(DISTINCT caller_address) FROM contract_calls
                WHERE contract_address = ?
            """, (contract_address,))
            user_count = cur.fetchone()
            user_count = user_count[0] if user_count else 0

        return metrics, user_count

    def get_all_metrics(self) -> Tuple[List[ContractMetrics], int]:
        """
        Retrieves all contract metrics from the database.
        Returns in the form of a list of ContractMetrics (metrics for each tracked contract)
        and then an int to represent the number of unique users across ALL contracts
        """

        with self.mutex:
            # Get contract metrics
            metrics_query = "SELECT * FROM contract_metrics"
            cur = self.conn.execute(metrics_query)
            rows = cur.fetchall()

            if not rows:
                return [], 0

            # Get total unique users
            cur = self.conn.execute("""
                SELECT COUNT(DISTINCT caller_address) FROM contract_calls
                """)
            user_count = cur.fetchone()
            user_count = user_count[0] if user_count else 0

        return [{
            "contract_address": row[0],
            "call_count": row[1],
            "total_amount": row[2],
            "call_chains": row[3]
        } for row in rows], user_count

        # return [dict(zip(columns, row), total_users=user_count) for row in rows]

    # def recompute_metrics(self):
    #     """Recomputes all contract metrics based on the current data in the database."""

    #     cur = self.conn.execute("""
    #         SELECT contract_address,
    #                 COUNT(*) AS call_count,
    #                 COUNT(DISTINCT caller_address) AS unique_user_count,
    #                 SUM(amount_usd) AS total_amount
    #         FROM contract_calls
    #         GROUP BY contract_address
    #     """)
    #     for row in cur.fetchall():
    #         self.update_contract_metrics(
    #             contract_address=row[0],
    #             call_count=row[1],
    #             unique_user_count=row[2],
    #             total_amount=row[3] or 0.0,
    #             call_chains=1  # currently static
    #         )

from datetime import datetime

if __name__ == "__main__":
    db = DB()
    # db.insert_contract_calls([
    #     {
    #         'tx_hash': "0x1",
    #         'block_number': 1,
    #         'contract_address': '0xabc',
    #         'caller_address': "0xa",
    #         'value': '10',
    #         'timestamp': datetime.now().isoformat(),
    #     },
    #     {
    #         'tx_hash': "0x2",
    #         'block_number': 1,
    #         'contract_address': '0xabc',
    #         'caller_address': "0xb",
    #         'value': '10',
    #         'timestamp': datetime.now().isoformat(),
    #     }
    # ])
    # # update metrics manually
    # db.update_contract_metrics('0xabc', 2, 20.0)

    # metrics = db.get_all_metrics()
    # print(metrics)
    # row = metrics[0]

    print(db.get_last_height("0x34B842D0AcF830134D44075DCbcE43Ba04286c12"))
    db.close()
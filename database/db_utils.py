import sqlite3
from typing import Optional, List, Dict
from types.t import ContractCall

class DB:
    def __init__(self, schema_file: str = "schema.sql", db_path: str = "hsk_data.db"):
        """Initializes the database connection and sets up the schema."""
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        with open(schema_file, "r") as f:
            self.conn.executescript(f.read())
        self.conn.commit()

        self.conn.row_factory = sqlite3.Row

    def close(self):
        """Closes the database connection."""
        self.conn.close()

    def insert_contract_call(self, call: ContractCall):
        """Inserts a new contract call into the database."""

        self.conn.execute("""
            INSERT INTO contract_calls
            (tx_hash, block_height, contract_address, caller_address, amount, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            call["tx_hash"],
            call["block_height"],
            call["contract_address"],
            call["caller_address"],
            call["amount"],
            call["timestamp"].isoformat()
        ))
        self.conn.commit()

    def insert_contract_calls(self, calls: List[ContractCall]):
        """
        Inserts multiple contract call records into the database.
        Each call must match the ContractCall TypedDict structure.
        """
        self.conn.executemany("""
            INSERT INTO contract_calls
            (tx_hash, block_height, contract_address, caller_address, amount, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [(
                call["tx_hash"],
                call["block_height"],
                call["contract_address"],
                call["caller_address"],
                call["amount"],
                call["timestamp"].isoformat()
            )
            for call in calls
        ])
        self.conn.commit()

    def get_last_height(self, contract_address: str) -> Optional[int]:
        """Retrieves the last processed block height for a given contract address."""

        cur = self.conn.execute("""
            SELECT last_processed_height FROM contract_states
            WHERE contract_address = ?
        """, (contract_address,))
        row = cur.fetchone()
        return row[0] if row else None

    def set_last_height(self, contract_address: str, block_height: int):
        """Updates the last processed block height for a given contract address."""

        self.conn.execute("""
            INSERT INTO contract_state (contract_address, last_processed_height)
            VALUES (?, ?)
            ON CONFLICT(contract_address) DO UPDATE SET last_processed_height = excluded.last_processed_height
        """, (contract_address, block_height))
        self.conn.commit()

    def update_contract_metrics(self,
        contract_address: str,
        call_count: int,
        total_amount: float,
        call_chains: int = 1
    ):
        """Updates contract metrics in the database."""

        self.conn.execute("""
            INSERT INTO contract_metrics
            (contract_address, call_count, total_amount, call_chains)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(contract_address) DO UPDATE SET
                call_count = excluded.call_count,
                total_amount_usd = excluded.total_amount_usd,
                call_chains = excluded.call_chains
        """, (
            contract_address,
            call_count,
            total_amount,
            call_chains
        ))
        self.conn.commit()

    def get_all_metrics(self) -> List[Dict]:
        """Retrieves all contract metrics from the database."""

        # Get total unique users
        cur = self.conn.execute("""
        SELECT COUNT(DISTINCT caller_address) FROM contract_calls
        """)
        user_count = cur.fetchone()[0] if cur.fetchone() else 0

        # Get contract metrics
        metrics_query = "SELECT * FROM contract_metrics ORDER BY block_number ASC"
        cur = self.conn.execute(metrics_query)
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()

        # Add user count to each row
        return [dict(zip(columns, row), total_users=user_count) for row in rows]

    def recompute_metrics(self):
        """Recomputes all contract metrics based on the current data in the database."""

        cur = self.conn.execute("""
            SELECT contract_address,
                    COUNT(*) AS call_count,
                    COUNT(DISTINCT caller_address) AS unique_user_count,
                    SUM(amount_usd) AS total_amount
            FROM contract_calls
            GROUP BY contract_address
        """)
        for row in cur.fetchall():
            self.update_contract_metrics(
                contract_address=row[0],
                call_count=row[1],
                unique_user_count=row[2],
                total_amount=row[3] or 0.0,
                call_chains=1  # currently static
            )

if __name__ == "__main__":
    db = DB()
    db.close()
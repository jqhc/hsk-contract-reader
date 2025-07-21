PRAGMA foreign_keys = ON;

-- Stores all contract calls and associated data
CREATE TABLE IF NOT EXISTS contract_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tx_hash TEXT NOT NULL UNIQUE,
    block_height INTEGER NOT NULL
    contract_address TEXT NOT NULL,
    caller_address TEXT NOT NULL,
    amount REAL NOT NULL,
    timestamp TEXT NOT NULL, -- ISO format
);

-- Stores metadata about each tracked contract
CREATE TABLE IF NOT EXISTS contract_states (
    contract_address TEXT PRIMARY KEY,
    last_processed_height INTEGER NOT NULL
);

-- Stores aggregated metrics for each contract for quick reference
CREATE TABLE IF NOT EXISTS contract_metrics (
    contract_address TEXT PRIMARY KEY,
    call_count INTEGER NOT NULL,
    total_amount REAL NOT NULL,
    call_chains INTEGER NOT NULL
);

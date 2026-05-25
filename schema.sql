-- Disable foreign key constraints during table creation to avoid order conflicts
PRAGMA foreign_keys = OFF;

-- 1. Users Table: Tracks core user state and whether they have turned on the feature
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    stock_back_enabled BOOLEAN DEFAULT 1 -- 1 = Yes (Opted-in), 0 = Standard Cashback
);

-- 2. Transactions Table: Logs daily card/UPI spending events
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY, -- Usually a UUID or UPI Ref No. from the gateway
    user_id INTEGER NOT NULL,
    amount DECIMAL(10, 2) NOT NULL, -- Never use FLOAT for currencies to avoid rounding bugs
    merchant_name TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 3. Rewards Ledger Table: Tracks "Monies" earned and their settlement status
CREATE TABLE IF NOT EXISTS rewards_ledger (
    reward_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    transaction_id TEXT NOT NULL,
    monies_earned INTEGER NOT NULL, -- E.g., ₹10 reward = 1000 Monies (stored as integers)
    status TEXT CHECK(status IN ('PENDING_BATCH', 'SETTLED', 'CLAWED_BACK')) DEFAULT 'PENDING_BATCH',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
);

-- 4. Asset Holdings Table: Tracks fractional gold ownership up to 4 decimal places
CREATE TABLE IF NOT EXISTS asset_holdings (
    user_id INTEGER PRIMARY KEY,
    gold_balance_grams DECIMAL(12, 4) DEFAULT 0.0000, -- High precision for micro-fractions
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

PRAGMA foreign_keys = ON;
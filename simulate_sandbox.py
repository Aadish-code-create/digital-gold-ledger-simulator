import sqlite3
import random
from decimal import Decimal, getcontext

# Set global precision context for Decimal math to prevent floating-point errors
getcontext().prec = 28

DB_FILE = "slice_sandbox.db"

def init_database():
    """Reads schema.sql and initializes the local SQLite database."""
    print("[1/4] Initializing database with schema.sql...")
    with sqlite3.connect(DB_FILE) as conn:
        with open("schema.sql", "r") as f:
            schema_script = f.read()
        conn.executescript(schema_script)
        conn.commit()

def seed_mock_data():
    """Seeds the database with a test user and mock transaction events."""
    print("[2/4] Seeding mock user and transaction data...")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        # Insert a mock user who has opted into Stock-Back
        cursor.execute("""
            INSERT OR IGNORE INTO users (user_id, name, email, stock_back_enabled) 
            VALUES (1, 'Aadis', 'aadis@example.com', 1)
        """)
        
        # Simulate 3 random merchant transactions
        mock_transactions = [
            ('TXN-99821', 1, 450.00, 'Zomato'),
            ('TXN-10293', 1, 1200.50, 'Starbucks'),
            ('TXN-44910', 1, 150.00, 'Blinkit')
        ]
        
        for txn_id, user_id, amount, merchant in mock_transactions:
            cursor.execute("""
                INSERT OR IGNORE INTO transactions (transaction_id, user_id, amount, merchant_name)
                VALUES (?, ?, ?, ?)
            """, (txn_id, user_id, amount, merchant))
            
            # Slice rule simulation: Earn 1% of transaction amount back in "Monies"
            # E.g., ₹450 transaction = 4.50 Rupees reward = 450 Monies (stored as an integer)
            monies_earned = int(amount * 1) 
            
            cursor.execute("""
                INSERT OR IGNORE INTO rewards_ledger (user_id, transaction_id, monies_earned, status)
                VALUES (?, ?, ?, 'PENDING_BATCH')
            """, (user_id, txn_id, monies_earned))
            
            # Ensure an asset profile row exists for the user
            cursor.execute("""
                INSERT OR IGNORE INTO asset_holdings (user_id, gold_balance_grams)
                VALUES (?, 0.0000)
            """, (user_id,))
            
        conn.commit()

def run_midnight_batch_engine():
    """
    THE CORE PITCH COMPONENT:
    Aggregates all pending reward points, simulates a single bulk institutional gold buy,
    and updates the internal fractional asset balances for users down to 4 decimals.
    """
    print("[3/4] Launching Midnight Batch Settlement Engine...")
    
    # Mocking live market data: Suppose 1 gram of 24K Digital Gold = ₹7,500
    GOLD_PRICE_PER_GRAM = Decimal('7500.00')
    MONIES_PER_RUPEE = Decimal('100.00')
    
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        # 1. Gather all users who have pending Monies and are opted into Stock-Back
        cursor.execute("""
            SELECT rl.user_id, SUM(rl.monies_earned) 
            FROM rewards_ledger rl
            JOIN users u ON rl.user_id = u.user_id
            WHERE rl.status = 'PENDING_BATCH' AND u.stock_back_enabled = 1
            GROUP BY rl.user_id
        """)
        pending_rewards = cursor.fetchall()
        
        if not pending_rewards:
            print("No pending balances found for settlement batch.")
            return

        total_batch_monies = 0
        user_allocations = {}

        for user_id, total_monies in pending_rewards:
            total_batch_monies += total_monies
            user_allocations[user_id] = Decimal(total_monies)

        # Calculate the single bulk pool value to execute via external API
        total_batch_rupees = Decimal(total_batch_monies) / MONIES_PER_RUPEE
        total_gold_purchased_grams = total_batch_rupees / GOLD_PRICE_PER_GRAM
        
        print(f" --- Total rewards aggregated across system: {total_batch_monies} Monies (₹{total_batch_rupees:.2f})")
        print(f" --- Executing institutional bulk purchase request to SafeGold: Buying {total_gold_purchased_grams:.6f} grams")

        # 2. Re-distribute down to the individual users' decimal ledger profiles
        for user_id, user_monies in user_allocations.items():
            user_rupees = user_monies / MONIES_PER_RUPEE
            # High-precision fractional calculation
            fractional_gold_earned = user_rupees / GOLD_PRICE_PER_GRAM
            
            # Format to exactly 4 decimal places as per DB architecture limits
            final_allocation = fractional_gold_earned.quantize(Decimal('0.0001'))
            
            print(f" --- Allocating {final_allocation} grams of gold to User ID: {user_id}")
            
            # Update user's wallet asset holding table
            cursor.execute("""
                UPDATE asset_holdings 
                SET gold_balance_grams = gold_balance_grams + ?, last_updated = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (str(final_allocation), user_id))
            
            # Mark these ledger line items as SETTLED so they aren't double-processed
            cursor.execute("""
                UPDATE rewards_ledger
                SET status = 'SETTLED'
                WHERE user_id = ? AND status = 'PENDING_BATCH'
            """, (user_id,))
            
        conn.commit()
        print("[Success] Batch complete and asset ledgers securely updated.")

def verify_results():
    """Utility function to print the final internal ledger state to the console."""
    print("[4/4] Fetching final production balances for review:")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT u.name, a.gold_balance_grams FROM asset_holdings a JOIN users u ON a.user_id = u.user_id")
        row = cursor.fetchone()
        if row:
            print(f"\n✨ User Portfolio State -> Name: {row[0]} | Gold Balance: {row[1]} grams ✨\n")

def process_merchant_refund(failed_transaction_id):
    """
    THE BUSINESS PROTECTION LAYER:
    Handles a transaction reversal safely without forcing an unwanted asset liquidation.
    Appends a negative ledger entry to claw back from the user's future transaction rewards.
    """
    print("\n⚠️ Alert: Processing a Merchant Refund Event...")
    
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        # 1. Find the original reward details for the refunded transaction
        cursor.execute("""
            SELECT user_id, monies_earned, status 
            FROM rewards_ledger 
            WHERE transaction_id = ?
        """, (failed_transaction_id,))
        original_reward = cursor.fetchone()
        
        if not original_reward:
            print(f"Error: Original transaction {failed_transaction_id} not found in rewards ledger.")
            return
            
        user_id, original_monies, status = original_reward
        clawback_monies = -original_monies # Convert to negative debt
        
        print(f" --- Original Transaction {failed_transaction_id} found. Points awarded: {original_monies} Monies.")
        print(f" --- Injecting clawback line item into ledger: {clawback_monies} Monies.")
        
        # 2. Insert a balancing negative entry into the ledger to cancel out the points
        refund_txn_id = f"REFUND-{failed_transaction_id}"
        cursor.execute("""
            INSERT INTO rewards_ledger (user_id, transaction_id, monies_earned, status)
            VALUES (?, ?, ?, 'PENDING_BATCH')
        """, (user_id, refund_txn_id, clawback_monies))
        
        conn.commit()
        print(f"[Success] Refund entry safely locked in ledger database.")

if __name__ == "__main__":
    # Clear old database files if you want a fresh run
    import os
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        
    init_database()
    seed_mock_data()
    
    # 1. First midnight batch runs (Allocates the initial gold balance)
    run_midnight_batch_engine()
    verify_results()
    
    # 2. Simulate user returning the Starbucks coffee order (TXN-10293)
    # Starbucks order was ₹1200.50, which generated 1200 Monies.
    process_merchant_refund('TXN-10293')
    
    # 3. Simulate another midnight batch processing the negative balance
    print("\n[Next Day] Launching Second Midnight Batch...")
    run_midnight_batch_engine()
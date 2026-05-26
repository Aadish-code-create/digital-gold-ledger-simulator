# **Digital-Gold-Ledger-Simulator(Monies turned into compounding asset!)**
Monies are really great but what if we were able to convert our monies into a compunding asset such as asset, 
digital gold or maybe a mutual fund.
We GenZ are desperate to make more money as we wish to spend more money. But, not all GenZs have a big balance, 
some aggressively look for ways to make the pockets heavy. 
Slice is really popular among youth for it's cash backs and according to LinkedIn News India, 
in the first four months of FY26 nearly 50% of the people invested in the markests
are under 30. This clearly shows that if the little rewards Slice gives as cash backs, if converted into some form of asset,
Youth will love it.

## What exactly the project do:

This project is a small simulation of a fintech-style reward and bulk-buy processing flow.
It focuses on understanding how transaction events, batching, and ledger allocation may work in a controlled sandbox environment.

### Project Files

- `schema.sql` → Defines the database schema used for storing transaction-related records.
- `simulate_sandbox.py` → Simulates the event flow, including logging, batch handling, and ledger-related processing.
- `slice_sandbox.db` → SQLite database used for storing sample simulated records during execution.

## System Architecture


```text
                     ┌──────────────────────────┐
                     │   User Transaction       │
                     └────────────┬─────────────┘
                                  │
                                  ▼
                     ┌──────────────────────────┐
                     │ Event Logger             │
                     │ (PENDING_BATCH)          │
                     └────────────┬─────────────┘
                                  │
                 ┌────────────────┴───────────────┐
                 │                                │
                 ▼                                ▼
     ┌────────────────────┐          ┌────────────────────┐
     │ Rewards Engine     │          │   Transaction DB   │
     │     (Async)        │          │   Persist Events   │
     └────────────────────┘          └─────────┬──────────┘
                                                │
                                                ▼
                                   ┌──────────────────────┐
                                   │ Midnight Batch       │
                                   │ Processor            │
                                   └─────────┬────────────┘
                                             │
                                             ▼
                                   ┌──────────────────────┐
                                   │ Aggregated Pool      │
                                   └─────────┬────────────┘
                                             │
                                             ▼
                                   ┌──────────────────────┐
                                   │ Provider API         │
                                   │ (SafeGold / Vault)   │
                                   └─────────┬────────────┘
                                             │
                                             ▼
                                   ┌──────────────────────┐
                                   │ Callback             │
                                   │ Confirmation         │
                                   └─────────┬────────────┘
                                             │
                                             ▼
                                   ┌──────────────────────┐
                                   │ Ledger Allocation    │
                                   │ Engine               │
                                   └──────────────────────┘
```

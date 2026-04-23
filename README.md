Personal Budget and Spending Assistant
COMP1110 Group Project — Semester 2, 2025-2026

## What is this?
Drawing from our analysis of existing market tools, we hope to develop a refined version that focus on three core factors: privacy, accessibility, and personalization. We use manual entry to ensure a more secure environment.
Our text-based assistant allows users to log spending, set category limits, and receive overspending alerts within a clean, user-friendly interface.

## How to run
Make sure you have Python 3 installed, then run:
```bash
python -m pip install -r requirements.txt
```
```bash
python interface.py
```

## File Overview
| File                        | Author                      | Purpose                                          |
|-----------------------------|----------------------------|--------------------------------------------------|
| datamodels.py               | Ekaterina Anufrieva         | Data models and file I/O                         |
| interface.py                | Insung Cho                  | Text-based interface and UI flow                 |
| summary_statictics.py       | Insung Cho                  | Summary statistics and category spending graph   |
| testdatagenerator.py        | Hongyi Wang                 | Test Data Generator                              |
| data/                       | Yaratha Nikhil Vardhan Reddy| Case study transaction, rules and budget files   |
| (more files TBA as groupmates complete their parts)                                                  |

## Data File Formats

### transactions.csv
Stores all spending transactions. Columns:
- date         : Date of transaction. Format: YYYY-MM-DD (e.g. 2024-06-01)
- amount       : Amount spent in HKD. Must be a positive number (e.g. 150.0)
- category     : Must be one of: Food, Rental, Transport, Shopping,
                 Entertainment, Health, Utilities, Subscriptions, Other
- description  : Short description of the spending (e.g. "Taxi ride home")
- notes        : Optional extra notes. Can be left blank.

Example:
date,amount,category,description,notes
2024-06-01,150.0,Food,Groceries at supermarket,Bought fruits and vegetables
2024-06-02,50.0,Transport,Taxi ride home,
2024-06-03,200.0,Entertainment,Concert tickets,Went to see a band live

### budget_rules.csv
Stores budget rules set by the user. Columns:
- category     : Category this rule applies to. Use "All" to apply to all
                 categories. Otherwise must be one of the categories above.
- limit_amount : Maximum amount allowed for this category in the given period.
                 Must be a positive number (e.g. 2000.0)
- period       : One of: daily, weekly, monthly, yearly
- alert        : "warn" = alert when approaching the limit (80% spent)
                 "exceed" = alert only when the limit has been exceeded
                 "velocity" = alert when a spending spike is detected in the last 3 days

Example:
category,limit_amount,period,alert
Food,2000.0,monthly,warn
Transport,500.0,weekly,exceed
All,10000.0,monthly,warn

### savings.csv
Stores savings records (deposits toward goals, with date and description).
Managed by GoalRecord class in datamodels.py.

Columns:
date : Date of savings deposit, format YYYY-MM-DD
amount : Amount saved in HKD (positive number)
description : Short note about this savings entry
Example:
date,amount,description
2024-06-01,500.0,Monthly savings deposit
2024-06-15,300.0,Bonus added to savings

### target.csv
Stores the overall savings target amount (single numeric value).
Used by Goal class to calculate progress percentage.

Content example (one line only):
10000.0

## Features Implemented in datamodels.py
* Data models: Transaction, BudgetRule, Goal, GoalRecord
* Save/load transactions to/from transactions.csv with validation
* Save/load budget rules to/from budget_rules.csv with validation
* Save/load savings records to/from savings.csv
* Save/load savings target to/from target.csv
* Spending calculation for past N days
* Data validation: date format, positive amounts, valid categories

## Running the Tests
To test the data model and file I/O independently, run:

    python datamodels.py

This will create sample transactions.csv and budget_rules.csv files in your
current folder and print the loaded results to the terminal.

To run the text-based interface, use:

    python interface.py

## New UI Features: Test Button & Goal Button

Two key interactive buttons have been implemented in the text-based interface to enhance usability and functionality:

### 1. Test Button

   The Test Button allows users to quickly validate the core functionality of the application without manual data entry.
   When selected, it auto-generates sample transactions and budget rules using the test data generator.
   Verifies that data loading, saving, and budget calculations work correctly.
   Helps users confirm the system is functioning as expected before entering real personal finance data.

### 2. Goal Button

   The Goal Button provides access to the savings goal management module.
   View current savings progress toward a financial target.
   Add new savings deposits and update the saved amount.
   Check goal completion percentage and remaining amount needed.
   Interacts with savings.csv and target.csv to store and retrieve goal data.

---

## Case Study Scenarios

The `data/` folder contains four case study scenarios used to evaluate the system. Each scenario includes a transactions file and a budget rules file that can be loaded directly into the program.

| Scenario | Focus | Files |
|----------|-------|-------|
| Scenario 1 — Daily Food Budget | Student tracking HKD 50/day food spending | scenario1_transactions.csv, scenario1_budget_rules.csv |
| Scenario 2 — Subscription Creep | Detecting accumulated monthly subscription overspend | scenario2_transactions.csv, scenario2_budget_rules.csv |
| Scenario 3 — Emergency Health Spike | Sudden large health expenses triggering velocity alert | scenario3_transactions.csv, scenario3_budget_rules.csv |
| Scenario 4 — Student End-of-Month | Multiple categories simultaneously over budget | scenario4_transactions.csv, scenario4_budget_rules.csv |

### How to run a scenario

Replace the active data files with the scenario files, then launch the program:

```bash
# Scenario 1
cp data/scenario1_transactions.csv transactions.csv
cp data/scenario1_budget_rules.csv budget_rules.csv
python interface.py
```

```bash
# Scenario 2
cp data/scenario2_transactions.csv transactions.csv
cp data/scenario2_budget_rules.csv budget_rules.csv
python interface.py
```

```bash
# Scenario 3
cp data/scenario3_transactions.csv transactions.csv
cp data/scenario3_budget_rules.csv budget_rules.csv
python interface.py
```

```bash
# Scenario 4
cp data/scenario4_transactions.csv transactions.csv
cp data/scenario4_budget_rules.csv budget_rules.csv
python interface.py
```

Once the program is running, press **S** to view the spending summary and **L** to view alerts. Press **Esc** to close a screen and **Q** to quit.

### Expected alerts per scenario

**Scenario 1** — WARNING and EXCEEDED fire for Food monthly spend (HKD 677 against limits of HKD 600 and HKD 650).

**Scenario 2** — EXCEEDED and WARNING fire for Subscriptions (HKD 873 against limits of HKD 500 and HKD 400). VELOCITY fires for recent subscription activity. WARNING and EXCEEDED fire for overall All spending.

**Scenario 3** — EXCEEDED and WARNING fire for Health (HKD 1,675 against limits of HKD 500 and HKD 400). VELOCITY fires detecting HKD 680 spent on Health in the last 3 days against a daily baseline of HKD 6.67.

**Scenario 4** — WARNING and EXCEEDED fire simultaneously for Food, Shopping, and Entertainment. WARNING fires for overall All spending approaching the monthly limit.

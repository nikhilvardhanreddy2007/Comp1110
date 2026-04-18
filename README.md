# Personal Budget and Spending Assistant
COMP1110 Group Project — Semester 2, 2025-2026

## What is this?
A text-based personal budget assistant that lets users log their spending,
set budget limits per category, and get alerts when they are overspending.

## How to run
Make sure you have Python 3 installed, then run:
```bash
python -m pip install -r requirements.txt
```
```bash
python interface.py
```

## File Overview
| File                | Author              | Purpose                              |
|---------------------|---------------------|--------------------------------------|
| datamodels.py       | Ekaterina Anufrieva | Data models and file I/O             |
| interface.py        | Insung Cho          | Text-based interface and UI flow     |
| testdatagenerator.py| Hongyi Wang         | Test Data Generator                  |
| (more files TBA as groupmates complete their parts)                      |

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

**Features Implemented in datamodels.py**
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

1. Test Button

   The Test Button allows users to quickly validate the core functionality of the application without manual data entry.
   When selected, it auto-generates sample transactions and budget rules using the test data generator.
   Verifies that data loading, saving, and budget calculations work correctly.
   Helps users confirm the system is functioning as expected before entering real personal finance data.

2. Goal Button

   The Goal Button provides access to the savings goal management module.
   View current savings progress toward a financial target.
   Add new savings deposits and update the saved amount.
   Check goal completion percentage and remaining amount needed.
   Interacts with savings.csv and target.csv to store and retrieve goal data.

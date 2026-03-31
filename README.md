# Personal Budget and Spending Assistant
COMP1110 Group Project — Semester 2, 2025-2026

## What is this?
A text-based personal budget assistant that lets users log their spending,
set budget limits per category, and get alerts when they are overspending.

## How to run
Make sure you have Python 3 installed, then run:
    python main.py 

## File Overview
| File                | Author              | Purpose                              |
|---------------------|---------------------|--------------------------------------|
| datamodels.py       | Ekaterina Anufrieva | Data models and file I/O             |
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

## Running the Tests
To test the data model and file I/O independently, run:
    python datamodels.py

This will create sample transactions.csv and budget_rules.csv files in your
current folder and print the loaded results to the terminal.

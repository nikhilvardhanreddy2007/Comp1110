#Personal Budget and Savings Assistant
#Author: Ekaterina Anufrieva
#Responsible for: Data Model & File I/O


import csv
import os
from datetime import datetime

#Section 1: Category List 

CATEGORIES = [
    "Food",
    "Rental",
    "Transport",
    "Shopping",
    "Entertainment",
    "Health",
    "Utilities",
    "Subscriptions",
    "Other"
] 

#Section 2: Data Models 
class Transaction: #Represents a single transaction
    def __init__(self, date, amount, category, description, notes=""): #this function is called when we create a new Transaction object
        self.date = date #str: format: YYYY-MM-DD
        self.amount = amount #float: Amount spent. Positive number. In HKD.
        self.category = category #str: One of the categories from the list above
        self.description = description #str: A brief description of the spending
        self.notes = notes #str: Optional extra notes. Can be left empty

    def to_dict(self): #Convert the transaction to a dictionary for easy saving to CSV
        return {
            "date": self.date,
            "amount": self.amount,
            "category": self.category,
            "description": self.description,
            "notes": self.notes
        }

    @staticmethod #Means this method an be called on the class itself
    def from_dict(data): #Useful for loading transactions from CSV, where each row is a dictionary
        return Transaction(
            date=data["date"],
            amount=float(data["amount"]),
            category=data["category"],
            description=data["description"],
            notes=data["notes"]
        )

class BudgetRule: #Represents a budget rule for a specific category and time period (e.g., "Food" category with a monthly limit of 2000 HKD)
    def __init__(self, category, limit_amount, period, alert): #Represents a budget rule for a specific category and time period
        self.category = category #str: One of the categories from the list above
        self.limit_amount = limit_amount #float: The maximum amount allowed for this category in the specified period
        self.period = period #str: "weekly", "monthly", "daily" or "yearly"
        self.alert = alert #str: "warn" or "exceed" - whether to warn the user when they are approaching the limit or only alert when they have exceeded it

    def to_dict(self): #Convert the budget rule to a dictionary for easy saving to CSV
        return {
            "category": self.category,
            "limit_amount": self.limit_amount,
            "period": self.period,
            "alert": self.alert
        }

    @staticmethod
    def from_dict(data): 
        return BudgetRule(
            category=data["category"], 
            limit_amount=float(data["limit_amount"]),
            period=data["period"],
            alert=data["alert"]
        )

#Section3: File I/O - Transactions
def save_transactions(transactions, filename="transactions.csv"): #Saves a list of Transaction objects to a CSV file
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["date", "amount", "category", "description", "notes"])
        writer.writeheader() #Write the header row
        for transaction in transactions:
            writer.writerow(transaction.to_dict()) #Write each transaction as a row in the CSV

    print(f"[Info] Saved {len(transactions)} transactions to {filename}.")

def load_transactions(filename="transactions.csv"): #Loads transactions from a CSV file and returns a list of Transaction objects
    transactions = []
    if not os.path.exists(filename): 
        print(f"[Notice]No transactions file found at {filename}. Starting with an empty list.")
        return transactions #Return an empty list if the file doesn't exist
    
    with open(filename, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        
        if reader.fieldnames is None:
            print(f"[Notice]Transactions file at {filename} is empty.")
            return transactions #Return an empty list if the file is empty
        
        for i, row in enumerate(reader, start=2): #Start at 2 to account for the header row
            try:
                date = row["date"].strip() 
                datetime.strptime(date, "%Y-%m-%d") #Validate date format

                amount = float(row["amount"].strip()) #Validate amount can be converted to float
                if amount < 0:
                    raise ValueError("Amount cannot be negative")
                
                category = row["category"].strip()
                if category not in CATEGORIES:
                    print(f"[Warning]Row {i}: Unknown category '{category}'. Keeping it as is.")

                description = row["description"].strip()
                notes = row.get("notes", "").strip() #Notes can be optional, so we use get() to avoid KeyError

                transactions.append(Transaction(date, amount, category, description, notes))

            except (ValueError, KeyError) as e:
                print(f"[Warning] Row {i} is invalid and will be skipped: {e}")

            

    print(f"[Info] Loaded {len(transactions)} transactions from {filename}.")
    return transactions

#Section 4: File I/O - Budget Rules
def save_budget_rules(rules, filename="budget_rules.csv"): #Saves a list of BudgetRule objects to a CSV file
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["category", "limit_amount", "period", "alert"])
        writer.writeheader() #Write the header row
        for rule in rules:
            writer.writerow(rule.to_dict()) #Write each budget rule as a row in the CSV

    print(f"[Info] Saved {len(rules)} budget rules to {filename}.")

def load_budget_rules(filename="budget_rules.csv"): #Loads budget rules from a CSV file and returns a list of BudgetRule objects
    rules =[]

    if not os.path.exists(filename):
        print(f"[Notice]No budget rules file found at {filename}. No rules loaded. ")
        return rules #Return an empty list if the file doesn't exist
    
    with open(filename, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            print(f"[Notice]Budget rules file at {filename} is empty.")
            return rules #Return an empty list if the file is empty
        
        for i, row in enumerate(reader, start=2): #Start at 2 to account for the header row
            try: #Validates the data before creating a BudgetRule object, and skips any rows that are invalid
                category = row["category"].strip()
                if category != "All" and category not in CATEGORIES: #Allow "All" as a special category for rules that apply to all categories
                    raise ValueError(f"Unknown category '{category}'")
                
                period = row["period"].strip().lower()

                if period not in ["weekly", "monthly", "daily", "yearly"]:
                    raise ValueError(f"Invalid period '{period}'. Must be one of: weekly, monthly, daily, yearly.")
                
                limit_amount = float(row["limit_amount"].strip()) #Validate limit_amount can be converted to float
                if limit_amount <= 0:
                    raise ValueError("Limit amount must be more than zero.")
                
                alert = row["alert"].strip().lower()
                if alert not in ["warn", "exceed"]:
                    raise ValueError(f"Invalid alert value '{alert}'. Must be 'warn' or 'exceed'.")
                
                rules.append(BudgetRule(category, limit_amount, period, alert))

            except (ValueError, KeyError) as e: #Catches both ValueError (for invalid data) and KeyError (for missing fields) and prints a warning message, then continues to the next row
                print(f"[Warning] Row {i} in budget rules file is invalid and will be skipped: {e}")

    print(f"[Info] Loaded {len(rules)} budget rules from {filename}.")
    return rules

#Section 5: Test Blocks (to test the code in this file, can be removed later)
if __name__ == "__main__":
    #Test saving and loading transactions
    test_transactions = [
        Transaction("2024-06-01", 150.0, "Food", "Groceries at supermarket", "Bought fruits and vegetables"),
        Transaction("2024-06-02", 50.0, "Transport", "Taxi ride home", ""),
        Transaction("2024-06-03", 200.0, "Entertainment", "Concert tickets", "Went to see a band live")
    ]
    save_transactions(test_transactions)
    loaded_transactions = load_transactions()
    for t in loaded_transactions:
        print(t.to_dict())

    #Test saving and loading budget rules
    test_rules = [
        BudgetRule("Food", 2000.0, "monthly", "warn"),
        BudgetRule("Transport", 500.0, "weekly", "exceed"),
        BudgetRule("All", 10000.0, "monthly", "warn") #A rule that applies to all categories
    ]
    save_budget_rules(test_rules)
    loaded_rules = load_budget_rules()
    for r in loaded_rules:
        print(r.to_dict())

        

               
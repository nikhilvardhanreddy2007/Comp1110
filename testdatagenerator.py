import datamodels
from datetime import datetime, timedelta
import random
CATEGORY_DATA = {
    "Food" : (50, 200),
    "Transport": (1, 300),
    "Shopping": (1, 1000),
    "Entertainment": (1, 1500),
    "Health": (100, 1000),
    "Utilities": (1, 200),
    "Subscriptions": (1, 200),
    "Other" : (1, 1000)
}
RULE_CATEGORY_DATA = {
    "Food" : (2000, 4000),
    "Transport": (500, 1600),
    "Shopping": (1000, 3000),
    "Entertainment": (1000, 2000),
    "Utilities": (500, 1000),
    "Subscriptions": (500, 1500),
    "Other" : (100, 2000)
}
PERIOD_MULTIPLIERS = {
    "daily": 1.0 / 30.0,
    "weekly": 1.0 / 4.0,
    "monthly": 1.0,
    "yearly": 12.0
}
def test_data_generator(n):
    testData = []
    current_date = datetime.now()
    rental_min, rental_max = CATEGORY_DATA.get("Rental", (6000, 15000))
    rental_amount = float(random.randint(rental_min, rental_max))
    
    testData.append(datamodels.Transaction(
        current_date.strftime("%Y-%m-%d"),
        rental_amount,
        "Rental",
        "Monthly Apartment Rent",
        "Fixed major expense"
    ))
    for i in range(n-1):
        days_to_add = random.randint(0, 2)
        current_date -= timedelta(days=days_to_add)

        category = random.choice(list(CATEGORY_DATA.keys()))

        min_val, max_val = CATEGORY_DATA[category]
        amount = float(random.randint(min_val, max_val))
        
        testData.append(datamodels.Transaction(
            current_date.strftime("%Y-%m-%d"),
            amount,
            category,
            f"Generated {category} expense", 
            "Auto-generated test data"))
    datamodels.save_transactions(testData, filename="transactions.csv")

def budget_rules_generator(n):
    rules = []
    total_monthly_budget = 0
    rule_list = list(RULE_CATEGORY_DATA.keys())
    for i in range(n):
        category = random.choice(rule_list)
        rule_list.remove(category)
        min_val, max_val = RULE_CATEGORY_DATA[category]
        original_amount = float(random.randint(min_val, max_val))
        
        period = random.choice(list(PERIOD_MULTIPLIERS.keys()))

        final_amount = original_amount * PERIOD_MULTIPLIERS[period]
        total_monthly_budget += final_amount
        
        alert = random.choice(["warn", "exceed", "velocity"])

        rule = datamodels.BudgetRule(category, final_amount, period, alert)
        rules.append(rule)
    rules.append(datamodels.BudgetRule("All", float(f"{total_monthly_budget + 10000:.3g}"), "Monthly", "Warn"))
    datamodels.save_budget_rules(rules, filename="budget_rules.csv")

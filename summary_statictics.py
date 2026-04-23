from statistics import median

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header, Static


def format_money(amount):
    return f"HKD {amount:.2f}"


def add_amount(grouped_amounts, key, amount):
    grouped_amounts[key] = grouped_amounts.get(key, 0.0) + amount


def percent_of_total(amount, total):
    if total == 0:
        return "0.0%"
    return f"{amount / total * 100:.1f}%"


def make_bar(amount, max_amount, width=24):
    if max_amount <= 0:
        return "░" * width

    filled = round((amount / max_amount) * width)
    if amount > 0:
        filled = max(1, filled)
    filled = max(0, min(width, filled))
    return "█" * filled + "░" * (width - filled)


def describe_transaction(transaction):
    return (
        f"{transaction.date} | {transaction.category} | "
        f"{format_money(transaction.amount)} | {transaction.description}"
    )


def build_summary_report(transactions, category_filter="All"):
    transactions = list(transactions)

    if not transactions:
        return f"No transactions found for {category_filter}."

    amounts = [transaction.amount for transaction in transactions]
    total_spent = sum(amounts)
    average_spend = total_spent / len(transactions)
    median_spend = median(amounts)
    smallest_transaction = min(transactions, key=lambda transaction: transaction.amount)
    largest_transaction = max(transactions, key=lambda transaction: transaction.amount)
    dates = sorted(transaction.date for transaction in transactions)

    totals_by_category = {}
    totals_by_month = {}

    for transaction in transactions:
        add_amount(totals_by_category, transaction.category, transaction.amount)
        add_amount(totals_by_month, transaction.date[:7], transaction.amount)

    category_totals = sorted(
        totals_by_category.items(), key=lambda item: (-item[1], item[0])
    )

    lines = [
        "Summary Statistics",
        f"Filter: {category_filter}",
        f"Date range: {dates[0]} to {dates[-1]}",
        "",
        "Overall",
        f"- Transactions: {len(transactions)}",
        f"- Total spent: {format_money(total_spent)}",
        f"- Average spend: {format_money(average_spend)}",
        f"- Median spend: {format_money(median_spend)}",
        f"- Smallest transaction: {describe_transaction(smallest_transaction)}",
        f"- Largest transaction: {describe_transaction(largest_transaction)}",
        "",
        "Spending by category",
    ]

    longest_category_name = max(len(category) for category, _ in category_totals)

    for category, amount in category_totals:
        category_name = category.ljust(longest_category_name)
        amount_text = format_money(amount).rjust(12)
        percent_text = percent_of_total(amount, total_spent).rjust(6)
        bar = make_bar(amount, total_spent)
        lines.append(f"- {category_name} | {bar} | {amount_text} | {percent_text}")

    month_totals = sorted(totals_by_month.items())
    longest_month_name = max(len(month) for month, _ in month_totals)

    lines.extend(["", "Spending by month"])

    for month, amount in month_totals:
        month_name = month.ljust(longest_month_name)
        amount_text = format_money(amount).rjust(12)
        percent_text = percent_of_total(amount, total_spent).rjust(6)
        bar = make_bar(amount, total_spent)
        lines.append(f"- {month_name} | {bar} | {amount_text} | {percent_text}")

    return "\n".join(lines)


class SummaryStatisticsScreen(Screen[None]):
    BINDINGS = [("escape", "close", "Close"), ("q", "close", "Close")]
    CSS = "#summary-body { padding: 1 2; overflow: auto; }"

    def __init__(self, transactions, category_filter):
        super().__init__()
        self.report = build_summary_report(transactions, category_filter)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Static(self.report, id="summary-body")
        yield Footer()

    def on_mount(self):
        self.title = "Summary Statistics"

    def action_close(self):
        self.dismiss()

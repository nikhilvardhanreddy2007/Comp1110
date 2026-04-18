import os
from datetime import date, datetime, timedelta

import testdatagenerator
import datamodels
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Select,
    Static,
)

from datamodels import (
    CATEGORIES,
    BudgetRule,
    Transaction,
    load_budget_rules,
    load_transactions,
    load_savings,
    load_goal_target,
    save_budget_rules,
    save_transactions,
    save_savings,
    save_goal_target
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRANSACTIONS_FILE = os.path.join(BASE_DIR, "transactions.csv")
BUDGET_RULES_FILE = os.path.join(BASE_DIR, "budget_rules.csv")
SAVING_FILE = os.path.join(BASE_DIR, "savings.csv")
TARGET_FILE = os.path.join(BASE_DIR, "target.csv")

CATEGORY_FILTER_OPTIONS = ["All"] +list(testdatagenerator.RULE_CATEGORY_DATA.keys())
BUDGET_PERIOD_OPTIONS = ["daily", "weekly", "monthly", "yearly"]
ALERT_MODE_OPTIONS = ["warn", "exceed", "velocity"]
MODAL_CSS = """
Screen { align: center middle; }
#dialog { width: 60; max-width: 90%; height: auto; border: round $accent; padding: 1 2; background: $surface; }
.title { text-style: bold; margin-bottom: 1; }
Label { margin-top: 1; }
.buttons { height: auto; margin-top: 1; }
Button { margin-right: 1; }
"""


def build_select_options(values):
    return [(value, value) for value in values]


def parse_date_input(raw_value, allow_blank=False):
    text = str(raw_value).strip()
    if not text:
        if allow_blank:
            return None
        raise ValueError("Date is required.")

    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("Use YYYY-MM-DD.") from exc


def parse_amount_input(raw_value):
    try:
        amount = float(str(raw_value).strip())
    except ValueError as exc:
        raise ValueError("Amount must be a number.") from exc

    if amount <= 0:
        raise ValueError("Amount must be positive.")
    return amount


def build_transaction(form_data):
    description = str(form_data["description"]).strip()
    if not description:
        raise ValueError("Description is required.")

    return Transaction(
        parse_date_input(form_data["date"]).isoformat(),
        parse_amount_input(form_data["amount"]),
        str(form_data["category"]),
        description,
        str(form_data["notes"]).strip(),
    )


def build_date_filter(form_data):
    start_date = parse_date_input(form_data["start"], allow_blank=True)
    end_date = parse_date_input(form_data["end"], allow_blank=True)

    if start_date and end_date and start_date > end_date:
        raise ValueError("Start date cannot be after end date.")

    return start_date, end_date


def build_budget_rule(form_data):
    return BudgetRule(
        str(form_data["category"]),
        parse_amount_input(form_data["limit"]),
        str(form_data["period"]),
        str(form_data["alert"]),
    )


def transaction_date(transaction):
    return datetime.strptime(transaction.date, "%Y-%m-%d").date()


def filter_transactions(
    transactions, category_filter="All", start_date=None, end_date=None
):
    matching_transactions = []

    for transaction in transactions:
        spending_date = transaction_date(transaction)

        if (
            category_filter not in (None, "All")
            and transaction.category != category_filter
        ):
            continue
        if start_date and spending_date < start_date:
            continue
        if end_date and spending_date > end_date:
            continue

        matching_transactions.append(transaction)

    return sorted(
        matching_transactions,
        key=lambda transaction: (
            transaction.date,
            transaction.category,
            transaction.description,
        ),
    )


def get_period_range(period, today):
    if period == "daily":
        return today, today

    if period == "weekly":
        week_start = today - timedelta(days=today.weekday())
        return week_start, week_start + timedelta(days=6)

    if period == "monthly":
        month_start = today.replace(day=1)
        next_month_start = month_start.replace(
            year=month_start.year + (month_start.month == 12),
            month=1 if month_start.month == 12 else month_start.month + 1,
            day=1,
        )
        return month_start, next_month_start - timedelta(days=1)

    return today.replace(month=1, day=1), today.replace(month=12, day=31)


def build_summary_report(transactions, category_filter):
    if not transactions:
        return "No transactions found."

    total_spent = sum(transaction.amount for transaction in transactions)
    largest_transaction = max(transactions, key=lambda transaction: transaction.amount)
    totals_by_category = {}
    totals_by_month = {}

    for transaction in transactions:
        totals_by_category[transaction.category] = (
            totals_by_category.get(transaction.category, 0.0) + transaction.amount
        )
        totals_by_month[transaction.date[:7]] = (
            totals_by_month.get(transaction.date[:7], 0.0) + transaction.amount
        )

    lines = [
        f"Category: {category_filter}",
        f"Transactions: {len(transactions)}",
        f"Total spent: HKD {total_spent:.2f}",
        f"Average: HKD {total_spent / len(transactions):.2f}",
        f"Largest: {largest_transaction.date} | {largest_transaction.category} | HKD {largest_transaction.amount:.2f}",
        "",
        "By category",
    ]
    lines.extend(
        f"- {category_name}: HKD {amount:.2f}"
        for category_name, amount in sorted(totals_by_category.items())
    )
    lines.extend(["", "By month"])
    lines.extend(
        f"- {month}: HKD {amount:.2f}"
        for month, amount in sorted(totals_by_month.items())
    )

    return "\n".join(lines)

def check_budget_velocity(transactions, rule):
    period_to_days = {
        "daily": 30,
        "weekly": 4,
        "monthly": 1,
        "yearly": 1/12
    }
    
    three_day_spend = datamodels.get_spending_for_past_days(transactions, rule.category, 3)
    
    budget_ratio = three_day_spend / (rule.limit_amount * period_to_days[rule.period])
    
    if three_day_spend > 0 and budget_ratio > 1/10:
        return True
    return False

def build_alert_report(transactions, rules, today):
    lines = []
    period_to_days = {
            "daily": 1,
            "weekly": 1/7,
            "monthly": 1/30,
            "yearly": 1/365
        }
    for rule in rules:
        period_start, period_end = get_period_range(rule.period, today)
        relevant_transactions = filter_transactions(
            transactions,
            None if rule.category == "All" else rule.category,
            period_start,
            period_end,
        )
        spent_amount = sum(transaction.amount for transaction in relevant_transactions)

        if rule.alert == "exceed" and spent_amount > rule.limit_amount:
            status_label = "EXCEEDED"
        elif rule.alert == "warn" and spent_amount >= rule.limit_amount * 0.8:
            status_label = "WARNING"
        elif rule.alert == "velocity" and check_budget_velocity(transactions, rule):
            status_label = "VELOCITY"
        else:
            continue
        if(status_label != "VELOCITY"):
            lines.extend(
                [
                    f"{status_label} - {rule.category} | {rule.period}",
                    f"Range: {period_start.isoformat()} to {period_end.isoformat()}",
                    f"Spent: HKD {spent_amount:.2f} / Limit: HKD {rule.limit_amount:.2f}",
                    "",
                ]
            )
        else:
            daily_baseline = rule.limit_amount * period_to_days[rule.period]
            three_days_transactions = filter_transactions(
                transactions,
                None if rule.category == "All" else rule.category,
                today - timedelta(days=3),
                today,
            )
            three_days_spent_amount = sum(transaction.amount for transaction in three_days_transactions)
            lines.extend(
                [
                    f"{status_label} - {rule.category} SPENDING SPIKE",
                    f"Unusual activity detected in the last 3 days.",
                    f"Recent Spend: HKD {three_days_spent_amount:.2f}",
                    f"Daily Avg: HKD {daily_baseline:.2f} (Expected: HKD {daily_baseline * 3:.2f} for 3 days)",
                    "",
                ]
            )

    return "\n".join(lines).strip() or "No alerts."


class ReportScreen(Screen[None]):
    BINDINGS = [("escape", "close", "Close"), ("q", "close", "Close")]
    CSS = "#body { padding: 1 2; overflow: auto; }"

    def __init__(self, title, content):
        super().__init__()
        self.report_title = title
        self.report_content = content

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Static(self.report_content, id="body")
        yield Footer()

    def on_mount(self):
        self.title = self.report_title

    def action_close(self):
        self.dismiss()


class ConfirmScreen(ModalScreen[bool]):
    BINDINGS = [("escape", "close", "Cancel")]
    CSS = MODAL_CSS

    def __init__(self, title, message, confirm_label="OK", confirm_variant="error"):
        super().__init__()
        self.dialog_title = title
        self.message = message
        self.confirm_label = confirm_label
        self.confirm_variant = confirm_variant

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static(self.dialog_title, classes="title")
            yield Static(self.message)
            with Horizontal(classes="buttons"):
                yield Button(self.confirm_label, id="yes", variant=self.confirm_variant)
                yield Button("Cancel", id="no")

    def on_mount(self):
        self.query_one("#yes", Button).focus()

    def action_close(self):
        self.dismiss(False)

    def on_button_pressed(self, event: Button.Pressed):
        self.dismiss(event.button.id == "yes")


class FormScreen(ModalScreen[object | None]):
    BINDINGS = [("escape", "close", "Cancel")]
    CSS = MODAL_CSS

    def __init__(self, title, fields, submit_handler, submit_label="Save"):
        super().__init__()
        self.form_title = title
        self.form_fields = fields
        self.submit_handler = submit_handler
        self.submit_label = submit_label

        for field_name, _, widget in self.form_fields:
            widget.id = field_name

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static(self.form_title, classes="title")
            for _, label_text, widget in self.form_fields:
                yield Label(label_text)
                yield widget
            with Horizontal(classes="buttons"):
                yield Button(self.submit_label, id="submit", variant="primary")
                yield Button("Cancel", id="cancel")

    def on_mount(self):
        self.query_one(f"#{self.form_fields[0][0]}").focus()

    def action_close(self):
        self.dismiss(None)

    def collect_form_data(self):
        return {
            field_name: self.query_one(f"#{field_name}").value
            for field_name, _, _ in self.form_fields
        }

    def submit_form(self):
        try:
            self.dismiss(self.submit_handler(self.collect_form_data()))
        except ValueError as exc:
            self.notify(str(exc), severity="error")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "submit":
            self.submit_form()
        else:
            self.dismiss(None)


def make_transaction_form():
    return FormScreen(
        "Add Transaction",
        [
            ("date", "Date", Input(date.today().isoformat())),
            ("amount", "Amount", Input(type="number")),
            (
                "category",
                "Category",
                Select(
                    build_select_options(CATEGORIES),
                    allow_blank=False,
                    value=CATEGORIES[0],
                ),
            ),
            ("description", "Description", Input()),
            ("notes", "Notes", Input()),
        ],
        build_transaction,
        "Add",
    )


def make_filter_form(start_date, end_date):
    return FormScreen(
        "Date Filter",
        [
            (
                "start",
                "Start date (YYYY-MM-DD, blank = none)",
                Input(
                    "" if start_date is None else start_date.isoformat(),
                    placeholder="YYYY-MM-DD",
                ),
            ),
            (
                "end",
                "End date (YYYY-MM-DD, blank = none)",
                Input(
                    "" if end_date is None else end_date.isoformat(),
                    placeholder="YYYY-MM-DD",
                ),
            ),
        ],
        build_date_filter,
        "Apply",
    )
def make_target_form(current_val):
    return FormScreen(
        "Edit Savings Target",
        [
            ("target", "New Target Amount", Input(str(current_val), type="number")),
        ],
        # The builder simply returns the float value from the input
        lambda d: float(d["target"]),
        "Update Target",
    )

def make_budget_rule_form():
    return FormScreen(
        "Add Budget Rule",
        [
            (
                "category",
                "Category",
                Select(
                    build_select_options(CATEGORY_FILTER_OPTIONS),
                    allow_blank=False,
                    value="All",
                ),
            ),
            ("limit", "Limit amount", Input(type="number")),
            (
                "period",
                "Period",
                Select(
                    build_select_options(BUDGET_PERIOD_OPTIONS),
                    allow_blank=False,
                    value="monthly",
                ),
            ),
            (
                "alert",
                "Alert",
                Select(
                    build_select_options(ALERT_MODE_OPTIONS),
                    allow_blank=False,
                    value="warn",
                ),
            ),
        ],
        build_budget_rule,
        "Add",
    )
def make_goal_record_form():
    return FormScreen(
        "Add Savings Record",
        [
            ("date", "Date", Input(date.today().isoformat())),
            ("amount", "Amount", Input(type="number", placeholder="Enter amount...")),
            ("description", "Goal Description", Input(placeholder="e.g., Vacation Fund")),
        ],
        build_goal_record, # Uses the builder above
        "Add",
    )
def build_goal_record(data):
    """Factory function for the FormScreen to create a GoalRecord."""
    return datamodels.GoalRecord(
        date=data["date"],
        amount=data["amount"],
        description=data["description"]
    )
class GoalScreen(ModalScreen):
    BINDINGS = [
        ("a", "add", "Add"),
        ("t", "change_target", "Target"), # New binding for convenience
        ("x", "delete", "Delete"),
        ("escape", "close", "Close"),
    ]

    def __init__(self, savings_list, target):
        super().__init__()
        self.savings_list = savings_list
        self.target = target

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Goals", classes="title")
            
            # Displays current target and a button to change it            
            with Vertical(id="stats_container"):
                yield Static(id="target_display")
                yield Static(id="goal_stats")
                yield Label("Savings History:")
                yield DataTable(id="savings_table")
            
            with Horizontal(classes="buttons"):
                yield Button("Edit Target", id="edit_target", variant="default")
                yield Button("Add Record", id="add", variant="primary")
                yield Button("Delete", id="delete", variant="error")
                yield Button("Close", id="close")

    def on_mount(self):
        table = self.query_one("#savings_table", DataTable)
        table.add_columns("Date", "Amount", "Description")
        table.cursor_type = "row"
        self.update_ui()

    def update_ui(self):
        # Update the Target display label
        self.query_one("#target_display", Static).update(f"Current Target: HKD {self.target:.2f}")

        total_saved = sum(s.amount for s in self.savings_list)
        percent = (total_saved / self.target) * 100 if self.target > 0 else 0
        percent = min(100, percent)

        bar_width = 20
        filled_width = int((percent / 100) * bar_width)
        bar = "█" * filled_width + "░" * (bar_width - filled_width)

        stats_label = self.query_one("#goal_stats", Static)
        stats_label.update(
            f"Total Saved:    HKD {total_saved:.2f} / {self.target:.2f}\n"
            f"Progress:       {bar} {percent:.1f}%"
        )
        self.refresh_table()

    def refresh_table(self):
        table = self.query_one("#savings_table", DataTable)
        table.clear()
        for i, s in enumerate(self.savings_list):
            table.add_row(s.date, f"{s.amount:.2f}", s.description, key=str(i))

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "edit_target":
            self.action_change_target()
        elif event.button.id == "add":
            self.app.push_screen(make_goal_record_form(), self.handle_new_saving)
        elif event.button.id == "delete":
            self.action_delete()
        else:
            self.app.pop_screen()

    def action_change_target(self):
        # Using your existing FormScreen logic style
        self.app.push_screen(
            make_target_form(self.target), 
            self.handle_target_changed
        )

    def handle_target_changed(self, new_target):
        if new_target is not None:
            self.target = new_target
            save_goal_target(self.target, TARGET_FILE) # Save to local file
            self.update_ui()

    def handle_new_saving(self, record):
        if record:
            self.savings_list.append(record)
            save_savings(self.savings_list, SAVING_FILE)
            self.update_ui()


class BudgetScreen(ModalScreen[list[BudgetRule] | None]):
    BINDINGS = [
        ("a", "add", "Add"),
        ("x", "delete", "Delete"),
        ("escape", "close", "Close"),
        ("q", "close", "Close"),
    ]
    CSS = (
        MODAL_CSS
        + "#dialog { width: 80; height: 24; } #rules { height: 1fr; margin: 1 0; }"
    )

    def __init__(self, rules):
        super().__init__()
        self.draft_rules = rules

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static("Budget Rules", classes="title")
            yield DataTable(id="rules")
            with Horizontal(classes="buttons"):
                yield Button("Add", id="add", variant="primary")
                yield Button("Delete", id="delete", variant="error")
                yield Button("Close", id="close")

    def on_mount(self):
        table = self.query_one("#rules", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.add_columns("Category", "Limit", "Period", "Alert")
        self.refresh_rule_table()
        table.focus()

    def selected_rule_index(self):
        if not self.draft_rules:
            return None

        table = self.query_one("#rules", DataTable)
        return min(table.cursor_row, len(self.draft_rules) - 1)

    def refresh_rule_table(self, keep_row=0):
        table = self.query_one("#rules", DataTable)
        table.clear()

        for rule in self.draft_rules:
            table.add_row(
                rule.category, f"HKD {rule.limit_amount:.2f}", rule.period, rule.alert
            )

        if self.draft_rules:
            table.move_cursor(row=min(keep_row, len(self.draft_rules) - 1))

    def handle_rule_added(self, rule):
        if rule is None:
            return

        self.draft_rules.append(rule)
        self.refresh_rule_table(len(self.draft_rules) - 1)

    def handle_delete_confirmation(self, confirmed, rule):
        if confirmed:
            self.draft_rules.remove(rule)
            save_budget_rules(self.draft_rules, BUDGET_RULES_FILE)
            self.refresh_rule_table()

    def action_add(self):
        self.app.push_screen(make_budget_rule_form(), self.handle_rule_added)

    def action_delete(self):
        selected_row = self.selected_rule_index()
        if selected_row is None:
            self.notify("No budget rules selected.", severity="warning")
            return

        rule = self.draft_rules[selected_row]

        # Use push_screen with a callback to catch the boolean result
        self.app.push_screen(
            ConfirmScreen(
                "Delete budget rule?",
                f"{rule.category} | HKD {rule.limit_amount:.2f} | {rule.period} | {rule.alert}",
                "Delete",
            ),
            # CRITICAL: This second argument handles the 'confirmed' result
            lambda confirmed: self.handle_delete_confirmation(confirmed, rule)
        )

    def action_close(self):
        self.dismiss(self.draft_rules)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "add":
            self.action_add()
        elif event.button.id == "delete":
            self.action_delete()
        else:
            self.action_close()


class BudgetApp(App):
    TITLE = "Budget Assistant"
    CSS = """
    Screen { layout: vertical; }
    #main { height: 1fr; }
    #categories { width: 24; border: round $accent; }
    #table { border: round $accent; }
    """
    BINDINGS = [
        ("a", "add", "Add"),
        ("x", "delete", "Delete"),
        ("f", "filter", "Filter"),
        ("s", "summary", "Summary"),
        ("l", "alerts", "Alerts"),
        ("b", "budgets", "Budgets"),
        ("t", "test", "Test"),
        ("g", "goals", "Goals"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.transactions = load_transactions(TRANSACTIONS_FILE)
        self.budget_rules = load_budget_rules(BUDGET_RULES_FILE)
        self.savings = load_savings(SAVING_FILE)
        self.target = load_goal_target(TARGET_FILE)
        self.filter_start_date = None
        self.filter_end_date = None
        self.visible_transactions = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Horizontal(id="main"):
            yield ListView(
                *[ListItem(Label(name)) for name in CATEGORY_FILTER_OPTIONS],
                id="categories",
            )
            yield DataTable(id="table")
        yield Footer()

    def on_mount(self):
        table = self.query_one("#table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.add_columns("Date", "Category", "Amount", "Description")
        self.query_one("#categories", ListView).index = 0
        self.refresh_transaction_table()
        table.focus()

    def on_list_view_highlighted(self, _: ListView.Highlighted):
        self.refresh_transaction_table()

    def on_list_view_selected(self, _: ListView.Selected):
        self.query_one("#table", DataTable).focus()

    def current_category_filter(self):
        selected_index = self.query_one("#categories", ListView).index or 0
        return CATEGORY_FILTER_OPTIONS[selected_index]

    def selected_transaction(self):
        if not self.visible_transactions:
            return None

        row = min(
            self.query_one("#table", DataTable).cursor_row,
            len(self.visible_transactions) - 1,
        )
        return self.visible_transactions[row]

    def refresh_transaction_table(self, keep_row=0):
        table = self.query_one("#table", DataTable)
        self.visible_transactions = filter_transactions(
            self.transactions,
            self.current_category_filter(),
            self.filter_start_date,
            self.filter_end_date,
        )
        table.clear()

        for transaction in self.visible_transactions:
            table.add_row(
                transaction.date,
                transaction.category,
                f"HKD {transaction.amount:.2f}",
                transaction.description,
            )

        if self.visible_transactions:
            table.move_cursor(row=min(keep_row, len(self.visible_transactions) - 1))

    def handle_transaction_added(self, transaction):
        if transaction is None:
            return

        self.transactions.append(transaction)
        save_transactions(self.transactions, TRANSACTIONS_FILE)
        self.refresh_transaction_table(len(self.visible_transactions))
        self.notify("Transaction added.", severity="information")

    def handle_transaction_delete(self, confirmed, transaction, row):
        if not confirmed:
            return

        self.transactions.remove(transaction)
        save_transactions(self.transactions, TRANSACTIONS_FILE)
        self.refresh_transaction_table(row)
        self.notify("Transaction deleted.", severity="information")

    def handle_filter_applied(self, date_range):
        if date_range is None:
            return

        self.filter_start_date, self.filter_end_date = date_range
        self.refresh_transaction_table()
        self.notify("Filter updated.", severity="information")

    def handle_budget_rules_saved(self, rules):
        if rules is None or rules == self.budget_rules:
            return

        self.budget_rules = rules
        save_budget_rules(self.budget_rules, BUDGET_RULES_FILE)
        self.notify("Budget rules updated.", severity="information")

    def action_add(self):
        self.push_screen(make_transaction_form(), self.handle_transaction_added)

    def action_delete(self):
        selected_transaction = self.selected_transaction()
        if selected_transaction is None:
            self.notify("Nothing to delete.", severity="warning")
            return

        selected_row = self.query_one("#table", DataTable).cursor_row

        def handle_confirm(confirmed):
            self.handle_transaction_delete(
                confirmed, selected_transaction, selected_row
            )

        self.push_screen(
            ConfirmScreen(
                "Delete transaction?",
                (
                    f"{selected_transaction.date} | "
                    f"{selected_transaction.category} | "
                    f"HKD {selected_transaction.amount:.2f} | "
                    f"{selected_transaction.description}"
                ),
                "Delete",
            ),
            handle_confirm,
        )

    def action_filter(self):
        self.push_screen(
            make_filter_form(self.filter_start_date, self.filter_end_date),
            self.handle_filter_applied,
        )

    def action_summary(self):
        self.push_screen(
            ReportScreen(
                "Summary",
                build_summary_report(
                    self.visible_transactions, self.current_category_filter()
                ),
            )
        )
    def action_test(self):
        testdatagenerator.test_data_generator(12)
        testdatagenerator.budget_rules_generator(5)
        self.transactions = load_transactions(TRANSACTIONS_FILE)
        self.budget_rules = load_budget_rules(BUDGET_RULES_FILE)
        self.push_screen(
            ConfirmScreen(
                "Data Generation Complete",
                (
                    "Successfully generated 12 transaction records, 5 category budget rules and a ALL budget rule."
                ),
                "Got it",
            ),
        )
        self.refresh_transaction_table()
    def action_goals(self):
        self.target = load_goal_target(TARGET_FILE_FILE)
        self.push_screen(GoalScreen(self.savings, self.target))
    
    def action_alerts(self):
        self.push_screen(
            ReportScreen(
                "Alerts",
                build_alert_report(self.transactions, self.budget_rules, date.today()),
            )
        )

    def action_budgets(self):
        self.push_screen(
            BudgetScreen(self.budget_rules.copy()), self.handle_budget_rules_saved
        )


if __name__ == "__main__":
    BudgetApp().run()

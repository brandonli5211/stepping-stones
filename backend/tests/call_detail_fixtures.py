"""Calls used by the call detail tests, in the shape the #29 tables hold.

HVB-DEMO-06 is the Transfer money call on the Figma frame (from the #33 demo data, call a2f086d27b3a4f96).
HVB-DEMO-02 is a Check balance call with no mistakes.
"""

from dataclasses import replace

from app.domain.call_detail import CallRecord, ComparisonRow, StepRecord, SubCheck, TurnRecord

# Step descriptions as docs/procedures/schema3/transfer_money.json stores them (procedures.rules).
TRANSFER_DESCRIPTIONS = {
    "greet_and_open": "State the bank name and your own name, then ask how you can help.",
    "collect_transfer_amount": "Get the amount the caller wants to transfer, by asking or by confirming what the "
                               "caller said.",
    "collect_source_account": "Get the account the money comes from (checking or savings), by asking or by "
                              "confirming.",
    "collect_destination_account": "Get the account the money goes to (checking or savings), by asking or by "
                                   "confirming.",
    "submit_and_confirm_transfer": "Log the transfer correctly, then read back the amount, source and destination "
                                   "to confirm it is done.",
    "offer_further_help": "Ask whether the caller needs anything else.",
    "close": "Thank the caller and end the call.",
}

TRANSFER_TURNS = (
    (0.54, "agent", "[noise]"),
    (2.3, "agent", "thank you for calling harper valley national bank my name is david how can i help you today"),
    (10.09, "caller", "hi my name is john williams i would like to transfer money between my accounts"),
    (17.14, "agent", "okay"),
    (18.47, "agent", "and"),
    (21.07, "agent", "alright and what is the transfer amount"),
    (26.19, "caller", "from my checking account to my savings account the amount is a hundred and fourteen dollars"),
    (29.87, "agent", "[noise]"),
    (33.53, "agent", "okay and that was from your savings to your checking account"),
    (40.69, "caller", "yes"),
    (40.21, "agent", "okay"),
    (45.62, "caller", "[noise]"),
    (44.54, "agent", "okay so i've transferred one hundred and fourteen dollars from your savings account to your "
                     "checking account is there anything else i can help you with"),
    (52.99, "caller", "[noise]"),
    (55.93, "caller", "no that's it thank you have a good day"),
    (57.2, "agent", "thank you for calling you have a great day"),
)

COACHING = ('Next time, read the accounts back in the order the caller gave them: '
            '"So that\'s $114 from your checking to your savings, is that right?"')


def _done(position: int, key: str, name: str, points: int, turn: int, quote: str) -> StepRecord:
    return StepRecord(key, position, name, points, "completed", evidence_turn_idx=turn, evidence_quote=quote)


def transfer_money_call() -> CallRecord:
    turns = tuple(TurnRecord(i, who, t, text) for i, (t, who, text) in enumerate(TRANSFER_TURNS, 1))
    submit = StepRecord(
        "submit_and_confirm_transfer", 5, "Submit and confirm transfer", 55, "wrong",
        severity="critical", points_lost=55,
        detail="read back reversed. The caller asked checking → savings",
        evidence_turn_idx=9, evidence_quote="okay and that was from your savings to your checking account",
        coaching=COACHING,
        sub_checks=(
            SubCheck("logged_matches", "Logged values match what the caller asked", 40, "failed"),
            SubCheck("read_back", "Read back amount and both accounts", 15, "failed"),
        ),
        comparison=(
            ComparisonRow("transfer_amount", "114", "114", True),
            ComparisonRow("transfer_source_account", "checking", "savings", False),
            ComparisonRow("transfer_destination_account", "savings", "checking", False),
        ),
    )
    steps = (
        _done(1, "greet_and_open", "Greet and open", 5, 2, TRANSFER_TURNS[1][2]),
        _done(2, "collect_transfer_amount", "Collect transfer amount", 10, 6, "what is the transfer amount"),
        _done(3, "collect_source_account", "Collect source account", 10, 7, "from my checking account"),
        _done(4, "collect_destination_account", "Collect destination account", 10, 7, "to my savings account"),
        submit,
        _done(6, "offer_further_help", "Offer further help", 5, 13, "is there anything else i can help you with"),
        _done(7, "close", "Close", 5, 16, "thank you for calling you have a great day"),
    )
    steps = tuple(replace(s, description=TRANSFER_DESCRIPTIONS[s.key]) for s in steps)
    return CallRecord(
        id=6, external_id="a2f086d27b3a4f96", call_type="transfer_money", call_type_name="Transfer money",
        summary="The transfer was logged and read back with the accounts reversed, so the money went from savings "
                "to checking.",
        turns=turns, steps=steps,
    )


def check_balance_call() -> CallRecord:
    turns = (
        TurnRecord(1, "agent", 1.2, "thank you for calling harper valley bank"),
        TurnRecord(2, "caller", 4.0, "hi i want to check my checking balance"),
        TurnRecord(3, "agent", 7.5, "your checking balance is two hundred dollars"),
    )
    steps = (
        _done(1, "greet", "Greet", 10, 1, "thank you for calling harper valley bank"),
        _done(2, "collect_account_type", "Collect account type", 30, 2, "my checking balance"),
        _done(3, "tell_balance", "Tell the balance", 60, 3, "your checking balance is two hundred dollars"),
    )
    return CallRecord(
        id=2, external_id="hvb-check-balance", call_type="check_balance", call_type_name="Check balance",
        summary="Every step was done right.", turns=turns, steps=steps,
    )

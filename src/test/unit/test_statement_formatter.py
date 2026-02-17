import pandas as pd

from budget_analyser.domain.statement_formatter import (
    CitiStatementFormatter,
    DefaultStatementFormatter,
    DiscoverStatementFormatter,
    create_statement_formatter,
)


def _sample_statement() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Date": ["2025-01-01", "2025-01-02"],
            "Description": ["Grocery Store", "Gas Station"],
            "amount": [100.0, 50.0],
        }
    )


def test_factory_creates_expected_formatter() -> None:
    df = pd.DataFrame()
    mapping = {}
    assert isinstance(
        create_statement_formatter(account_name="citi", statement=df, column_mapping=mapping),
        CitiStatementFormatter,
    )
    assert isinstance(
        create_statement_formatter(
            account_name="discover", statement=df, column_mapping=mapping
        ),
        DiscoverStatementFormatter,
    )
    assert isinstance(
        create_statement_formatter(account_name="chase", statement=df, column_mapping=mapping),
        DefaultStatementFormatter,
    )


def test_citi_inverts_amounts() -> None:
    df = _sample_statement()
    mapping = {"Date": "transaction_date", "Description": "description", "amount": "amount"}
    formatter = create_statement_formatter(
        account_name="citi", statement=df, column_mapping=mapping
    )
    formatted = formatter.get_desired_format()
    assert (formatted["amount"] < 0).all()


def test_default_keeps_amounts_positive() -> None:
    df = _sample_statement()
    mapping = {"Date": "transaction_date", "Description": "description", "amount": "amount"}
    formatter = create_statement_formatter(
        account_name="chase", statement=df, column_mapping=mapping
    )
    formatted = formatter.get_desired_format()
    assert (formatted["amount"] > 0).all()

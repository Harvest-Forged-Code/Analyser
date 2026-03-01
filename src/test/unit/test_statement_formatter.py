from pathlib import Path

import pandas as pd

from budget_analyser.settings.ini_config import IniAppConfig
from budget_analyser.features.ingestion.formatters import (
    AppleStatementFormatter,
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
        create_statement_formatter(account_name="apple", statement=df, column_mapping=mapping),
        AppleStatementFormatter,
    )
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
    assert isinstance(
        create_statement_formatter(
            account_name="wellsfargo", statement=df, column_mapping=mapping
        ),
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


def test_apple_inverts_amounts() -> None:
    df = _sample_statement()
    mapping = {"Date": "transaction_date", "Description": "description", "amount": "amount"}
    formatter = create_statement_formatter(
        account_name="apple", statement=df, column_mapping=mapping
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


def test_wellsfargo_default_keeps_amounts() -> None:
    df = _sample_statement()
    mapping = {"Date": "transaction_date", "Description": "description", "amount": "amount"}
    formatter = create_statement_formatter(
        account_name="wellsfargo", statement=df, column_mapping=mapping
    )
    formatted = formatter.get_desired_format()
    assert (formatted["amount"] > 0).all()


def test_get_csv_column_names_returns_names_for_headerless(
    tmp_path: Path,
) -> None:
    ini_file = tmp_path / "test.ini"
    ini_file.write_text(
        "[wellsfargo_options]\n"
        "has_header = false\n"
        "column_names = date,amount,marker,empty,description\n"
    )
    config = IniAppConfig(path=ini_file)
    result = config.get_csv_column_names(account_name="wellsfargo")
    assert result == ["date", "amount", "marker", "empty", "description"]


def test_get_csv_column_names_returns_none_for_normal(
    tmp_path: Path,
) -> None:
    ini_file = tmp_path / "test.ini"
    ini_file.write_text("[apple_map]\ntransaction_date = Transaction Date\n")
    config = IniAppConfig(path=ini_file)
    result = config.get_csv_column_names(account_name="apple")
    assert result is None


def test_get_csv_column_names_returns_none_when_has_header_true(
    tmp_path: Path,
) -> None:
    ini_file = tmp_path / "test.ini"
    ini_file.write_text(
        "[mybank_options]\n"
        "has_header = true\n"
        "column_names = a,b,c\n"
    )
    config = IniAppConfig(path=ini_file)
    result = config.get_csv_column_names(account_name="mybank")
    assert result is None

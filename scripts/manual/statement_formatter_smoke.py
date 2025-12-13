"""
Test script for statement formatter classes
"""
# Dependencies
import pandas as pd
import sys
from pathlib import Path

# Ensure project root is on sys.path when running this script directly from source/Unitests.
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Internal Dependencies
from source.model.statement_formatter import (
    create_statement_formatter,
    CitiStatementFormatter,
    DiscoverStatementFormatter,
    DefaultStatementFormatter
)

def create_test_dataframe():
    """Create a test dataframe with sample data"""
    data = {
        'Date': ['2025-01-01', '2025-01-02', '2025-01-03'],
        'Description': ['Grocery Store', 'Gas Station', 'Restaurant'],
        'Debit': [100.0, 50.0, 75.0],
        'Credit': [0.0, 0.0, 0.0]
    }
    return pd.DataFrame(data)

def test_citi_formatter():
    """Test the CitiStatementFormatter"""
    print("\nTesting CitiStatementFormatter...")
    
    # Create test data
    df = create_test_dataframe()
    print("Original data:")
    print(df)
    
    # Create formatter
    formatter = create_statement_formatter(account_name='citi', statement=df)
    
    # Format data
    formatted_df = formatter.get_desired_format()
    
    print("\nFormatted data:")
    print(formatted_df)
    
    # Verify that amounts are negative (Citi-specific formatting)
    if all(formatted_df['amount'] < 0):
        print("✓ Citi-specific formatting applied correctly (amounts are negative)")
    else:
        print("✗ Citi-specific formatting failed (some amounts are not negative)")

def test_discover_formatter():
    """Test the DiscoverStatementFormatter"""
    print("\nTesting DiscoverStatementFormatter...")
    
    # Create test data
    df = create_test_dataframe()
    print("Original data:")
    print(df)
    
    # Create formatter
    formatter = create_statement_formatter(account_name='discover', statement=df)
    
    # Format data
    formatted_df = formatter.get_desired_format()
    
    print("\nFormatted data:")
    print(formatted_df)
    
    # Verify that amounts are negative (Discover-specific formatting)
    if all(formatted_df['amount'] < 0):
        print("✓ Discover-specific formatting applied correctly (amounts are negative)")
    else:
        print("✗ Discover-specific formatting failed (some amounts are not negative)")

def test_default_formatter():
    """Test the DefaultStatementFormatter"""
    print("\nTesting DefaultStatementFormatter...")
    
    # Create test data
    df = create_test_dataframe()
    print("Original data:")
    print(df)
    
    # Create formatter
    formatter = create_statement_formatter(account_name='chase', statement=df)
    
    # Format data
    formatted_df = formatter.get_desired_format()
    
    print("\nFormatted data:")
    print(formatted_df)
    
    # Verify that amounts are positive (no sign inversion)
    if all(formatted_df['amount'] > 0):
        print("✓ Default formatting applied correctly (amounts are positive)")
    else:
        print("✗ Default formatting failed (some amounts are not positive)")

def test_factory_function():
    """Test the create_statement_formatter factory function"""
    print("\nTesting create_statement_formatter factory function...")
    
    # Test with Citi
    formatter = create_statement_formatter(account_name='citi', statement=pd.DataFrame())
    if isinstance(formatter, CitiStatementFormatter):
        print("✓ Factory correctly created CitiStatementFormatter for 'citi'")
    else:
        print(f"✗ Factory created wrong formatter for 'citi': {type(formatter)}")
    
    # Test with Discover
    formatter = create_statement_formatter(account_name='discover', statement=pd.DataFrame())
    if isinstance(formatter, DiscoverStatementFormatter):
        print("✓ Factory correctly created DiscoverStatementFormatter for 'discover'")
    else:
        print(f"✗ Factory created wrong formatter for 'discover': {type(formatter)}")
    
    # Test with other bank
    formatter = create_statement_formatter(account_name='chase', statement=pd.DataFrame())
    if isinstance(formatter, DefaultStatementFormatter):
        print("✓ Factory correctly created DefaultStatementFormatter for 'chase'")
    else:
        print(f"✗ Factory created wrong formatter for 'chase': {type(formatter)}")

if __name__ == "__main__":
    print("Running statement formatter tests...")
    
    # Test the factory function
    test_factory_function()
    
    # Test individual formatters
    test_citi_formatter()
    test_discover_formatter()
    test_default_formatter()
    
    print("\nAll tests completed.")
# Statement Formatter Implementation Changes

## Overview

This document describes the changes made to implement a base formatter class and child classes for individual bank statements as requested in the issue.

## Changes Made

### 1. Base Formatter Class

Created an abstract base class `BaseStatementFormatter` that contains common functionality for formatting bank statements:

- Renamed the original `StatementFormatter` class to `BaseStatementFormatter`
- Made it an abstract base class by inheriting from ABC
- Added an abstract method `_bank_specific_formatting()` that child classes must implement
- Moved common formatting logic to the base class

### 2. Child Formatter Classes

Implemented three child classes for specific banks:

1. **CitiStatementFormatter**
   - Implements Citi-specific formatting
   - Inverts the sign of amounts (multiplies by -1)

2. **DiscoverStatementFormatter**
   - Implements Discover-specific formatting
   - Also inverts the sign of amounts (multiplies by -1)

3. **DefaultStatementFormatter**
   - Default implementation for banks that don't need special formatting
   - No additional formatting applied

### 3. Factory Function

Added a factory function `create_statement_formatter()` that creates the appropriate formatter based on the account name:

- Takes the same parameters as the formatter constructors
- Returns an instance of the appropriate formatter class based on the account name
- Simplifies client code by hiding the details of which formatter class to use

### 4. Updated Statements Class

Modified the `Statements` class to use the new factory function:

- Updated the import statement to import `create_statement_formatter` instead of `StatementFormatter`
- Updated the code in the `collect_transactions` method to use the factory function

## Benefits of the New Implementation

1. **Separation of Concerns**: Each bank's specific formatting logic is now encapsulated in its own class.
2. **Extensibility**: Adding support for a new bank is as simple as creating a new child class and updating the factory function.
3. **Maintainability**: Changes to one bank's formatting logic won't affect other banks.
4. **Code Reuse**: Common formatting logic is defined once in the base class and inherited by all child classes.

## Testing

A pytest unit test `tests/unit/test_statement_formatter.py` was created to verify the implementation:

- Tests the factory function to ensure it creates the correct formatter class
- Tests each formatter class to verify it applies the correct formatting
- Creates sample data and verifies the formatting results

## Future Improvements

1. Add more bank-specific formatters as needed
2. Enhance the test script with more comprehensive test cases
3. Consider using a configuration file to define bank-specific formatting rules
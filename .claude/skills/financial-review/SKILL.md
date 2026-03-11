---
name: financial-review
description: Finance Analyst reviews financial logic in code changes for accuracy, edge cases, and domain correctness
---

# Financial Logic Review

Have the Finance Analyst agent review code changes that affect financial calculations, budget logic, categorization, reporting, or forecasting.

## When to Use

- After implementing changes to any financial feature module
- Before merging code that touches budget calculations or forecasting
- When adding new categorization mappings or rules
- After modifying report generation logic
- When changing data ingestion or transaction processing

## Financial Feature Modules

These are the features that require financial review:

| Module | Financial Concern |
|--------|-------------------|
| `features/budget_goals/` | Budget calculations, earnings goals, spending limits |
| `features/forecasting/` | Expense projections, trend extrapolation |
| `features/trends/` | Spending velocity, burn rate analysis |
| `features/savings/` | Savings rate, goal progress, target tracking |
| `features/reporting/` | Monthly summaries, category totals, aggregations |
| `features/payments/` | Payment reconciliation, matching logic |
| `features/recurring/` | Recurring transaction detection, frequency analysis |
| `features/mappers/` | Category/cashflow keyword mappings |
| `features/net_worth/` | Account balances, liability tracking, net worth calculation |
| `features/ingestion/` | CSV parsing, amount sign conventions, date handling |

## Process

### Step 1: Identify Changed Financial Code

Run `git diff` to find modified files in financial feature modules:

```bash
git diff --name-only HEAD | grep -E 'features/(budget_goals|forecasting|trends|savings|reporting|payments|recurring|mappers|net_worth|ingestion)/'
```

### Step 2: Spawn Finance Analyst Agent

Launch the `finance-analyst` agent with:
- The list of changed files
- The git diff of those files
- Context about what the changes are intended to do

### Step 3: Review Checklist

The Finance Analyst validates against this checklist:

**Mathematical Accuracy**
- [ ] Budget totals are calculated correctly (sum of category amounts)
- [ ] Percentages are computed correctly (numerator/denominator, multiply by 100)
- [ ] Averages use the correct denominator (count of non-zero periods)
- [ ] Running totals accumulate correctly across periods

**Currency & Precision**
- [ ] No floating-point arithmetic for money (use Decimal or integer cents)
- [ ] Rounding is applied consistently (banker's rounding preferred)
- [ ] Currency formatting does not affect calculation values
- [ ] No precision loss in aggregation chains

**Date Boundaries**
- [ ] Month boundary calculations are correct (last day of month varies)
- [ ] Year transitions handled (December → January)
- [ ] Leap year edge cases considered
- [ ] Timezone effects on date-based grouping

**Empty/Zero Data**
- [ ] Zero-transaction periods do not cause division by zero
- [ ] Empty DataFrames return sensible defaults (not errors)
- [ ] New users with no history get appropriate empty-state responses
- [ ] Missing categories do not break report generation

**Negative Amounts**
- [ ] Credits and refunds handled correctly (sign conventions)
- [ ] Bank-specific sign conventions respected (Citi positive = charge, Discover negative = charge)
- [ ] Negative budget remaining is reported correctly (overspend)
- [ ] Net calculations handle mixed positive/negative values

**Categorization**
- [ ] Keyword matching is case-insensitive
- [ ] Uncategorized fallback works for unknown merchants
- [ ] Category totals match individual transaction sums
- [ ] No duplicate categorization (one transaction, one category)

**Forecasting**
- [ ] Projection assumptions are documented and reasonable
- [ ] Trend extrapolation has sensible limits (not projecting to infinity)
- [ ] Insufficient data produces a warning, not a garbage forecast
- [ ] Confidence intervals widen appropriately with projection distance

### Step 4: Report

The Finance Analyst produces a structured report:

```markdown
## Financial Review: [Feature/Change]

### Verdict: [PASS / CONCERNS / FAIL]

### Issues Found
| # | File:Line | Category | Severity | Description |
|---|-----------|----------|----------|-------------|
| 1 | service.py:45 | Calculation | HIGH | Division by zero when no transactions |
| 2 | models.py:23 | Precision | MEDIUM | Using float instead of Decimal for budget |

### Edge Cases Verified
| Scenario | Status | Notes |
|----------|--------|-------|
| Zero transactions in period | Handled | Returns empty report |
| Negative refund amounts | MISSING | Refunds counted as expenses |

### Recommendations
1. [Specific fix with code example]
2. [Additional test case to add]
```

## Rules

- Financial review is MANDATORY before merging changes to financial feature modules
- The Finance Analyst does not modify code — they review and recommend
- All issues rated HIGH severity must be fixed before merge
- Edge case testing must be verified, not assumed

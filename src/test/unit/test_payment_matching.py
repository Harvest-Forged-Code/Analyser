"""Tests for payment matching service."""

import pandas as pd
import pytest
from datetime import datetime

from budget_analyser.domain.payment_matching import (
    PaymentMatchingService,
    PaymentMatchResult,
    PaymentPair,
    create_payment_matcher,
)


class TestPaymentPair:
    """Tests for PaymentPair dataclass."""

    def test_net_amount_is_zero(self):
        pair = PaymentPair(
            payment_made_id=1,
            payment_confirmed_id=2,
            amount=100.0,
            payment_date=datetime(2024, 1, 1),
            confirmation_date=datetime(2024, 1, 2),
            days_apart=1,
            confidence=0.9,
        )
        assert pair.net_amount == 0.0


class TestPaymentMatchResult:
    """Tests for PaymentMatchResult dataclass."""

    def test_match_rate_all_matched(self):
        result = PaymentMatchResult(
            matched_pairs=[
                PaymentPair(
                    payment_made_id=1,
                    payment_confirmed_id=2,
                    amount=100.0,
                    payment_date=datetime(2024, 1, 1),
                    confirmation_date=datetime(2024, 1, 2),
                    days_apart=1,
                    confidence=0.9,
                )
            ],
            unmatched_payments=pd.DataFrame(),
            unmatched_confirmations=pd.DataFrame(),
        )
        assert result.match_rate == 100.0

    def test_match_rate_partial(self):
        result = PaymentMatchResult(
            matched_pairs=[
                PaymentPair(
                    payment_made_id=1,
                    payment_confirmed_id=2,
                    amount=100.0,
                    payment_date=datetime(2024, 1, 1),
                    confirmation_date=datetime(2024, 1, 2),
                    days_apart=1,
                    confidence=0.9,
                )
            ],
            unmatched_payments=pd.DataFrame({"amount": [50.0]}),
            unmatched_confirmations=pd.DataFrame(),
        )
        assert result.match_rate == 50.0

    def test_match_rate_none_matched(self):
        result = PaymentMatchResult(
            unmatched_payments=pd.DataFrame({"amount": [100.0]}),
            unmatched_confirmations=pd.DataFrame({"amount": [100.0]}),
        )
        assert result.match_rate == 0.0

    def test_total_matched_amount(self):
        result = PaymentMatchResult(
            matched_pairs=[
                PaymentPair(
                    payment_made_id=1, payment_confirmed_id=2,
                    amount=100.0,
                    payment_date=datetime(2024, 1, 1),
                    confirmation_date=datetime(2024, 1, 2),
                    days_apart=1, confidence=0.9,
                ),
                PaymentPair(
                    payment_made_id=3, payment_confirmed_id=4,
                    amount=200.0,
                    payment_date=datetime(2024, 1, 3),
                    confirmation_date=datetime(2024, 1, 4),
                    days_apart=1, confidence=0.9,
                ),
            ],
        )
        assert result.total_matched_amount == 300.0

    def test_is_fully_matched(self):
        fully_matched = PaymentMatchResult(
            matched_pairs=[
                PaymentPair(
                    payment_made_id=1, payment_confirmed_id=2,
                    amount=100.0,
                    payment_date=datetime(2024, 1, 1),
                    confirmation_date=datetime(2024, 1, 2),
                    days_apart=1, confidence=0.9,
                )
            ],
        )
        assert fully_matched.is_fully_matched

        not_fully_matched = PaymentMatchResult(
            unmatched_payments=pd.DataFrame({"amount": [100.0]}),
        )
        assert not not_fully_matched.is_fully_matched


class TestPaymentMatchingService:
    """Tests for PaymentMatchingService."""

    def test_exact_amount_same_day_match(self):
        service = PaymentMatchingService()

        payments = pd.DataFrame({
            "amount": [-100.0],
            "transaction_date": ["2024-01-15"],
        })
        confirmations = pd.DataFrame({
            "amount": [100.0],
            "transaction_date": ["2024-01-15"],
        })

        result = service.match_payments(
            payments_made=payments,
            payment_confirmations=confirmations,
        )

        assert len(result.matched_pairs) == 1
        assert result.matched_pairs[0].amount == 100.0
        assert result.matched_pairs[0].days_apart == 0

    def test_match_within_date_tolerance(self):
        service = PaymentMatchingService(max_days_apart=3)

        payments = pd.DataFrame({
            "amount": [-100.0],
            "transaction_date": ["2024-01-15"],
        })
        confirmations = pd.DataFrame({
            "amount": [100.0],
            "transaction_date": ["2024-01-18"],  # 3 days later
        })

        result = service.match_payments(
            payments_made=payments,
            payment_confirmations=confirmations,
        )

        assert len(result.matched_pairs) == 1
        assert result.matched_pairs[0].days_apart == 3

    def test_no_match_outside_date_tolerance(self):
        service = PaymentMatchingService(max_days_apart=3)

        payments = pd.DataFrame({
            "amount": [-100.0],
            "transaction_date": ["2024-01-15"],
        })
        confirmations = pd.DataFrame({
            "amount": [100.0],
            "transaction_date": ["2024-01-20"],  # 5 days later
        })

        result = service.match_payments(
            payments_made=payments,
            payment_confirmations=confirmations,
        )

        assert len(result.matched_pairs) == 0
        assert len(result.unmatched_payments) == 1
        assert len(result.unmatched_confirmations) == 1

    def test_no_match_different_amounts(self):
        service = PaymentMatchingService(amount_tolerance=0.01)

        payments = pd.DataFrame({
            "amount": [-100.0],
            "transaction_date": ["2024-01-15"],
        })
        confirmations = pd.DataFrame({
            "amount": [150.0],  # Different amount
            "transaction_date": ["2024-01-15"],
        })

        result = service.match_payments(
            payments_made=payments,
            payment_confirmations=confirmations,
        )

        assert len(result.matched_pairs) == 0

    def test_multiple_matches(self):
        service = PaymentMatchingService()

        payments = pd.DataFrame({
            "amount": [-100.0, -200.0, -300.0],
            "transaction_date": ["2024-01-15", "2024-01-16", "2024-01-17"],
        })
        confirmations = pd.DataFrame({
            "amount": [100.0, 200.0, 300.0],
            "transaction_date": ["2024-01-15", "2024-01-17", "2024-01-18"],
        })

        result = service.match_payments(
            payments_made=payments,
            payment_confirmations=confirmations,
        )

        assert len(result.matched_pairs) == 3
        assert result.is_fully_matched

    def test_partial_matches(self):
        service = PaymentMatchingService()

        payments = pd.DataFrame({
            "amount": [-100.0, -200.0],
            "transaction_date": ["2024-01-15", "2024-01-16"],
        })
        confirmations = pd.DataFrame({
            "amount": [100.0],
            "transaction_date": ["2024-01-15"],
        })

        result = service.match_payments(
            payments_made=payments,
            payment_confirmations=confirmations,
        )

        assert len(result.matched_pairs) == 1
        assert len(result.unmatched_payments) == 1

    def test_empty_inputs(self):
        service = PaymentMatchingService()

        result = service.match_payments(
            payments_made=pd.DataFrame(),
            payment_confirmations=pd.DataFrame(),
        )

        assert len(result.matched_pairs) == 0
        assert result.match_rate == 100.0  # Nothing to match

    def test_missing_columns(self):
        service = PaymentMatchingService()

        payments = pd.DataFrame({"other_column": [1, 2, 3]})
        confirmations = pd.DataFrame({"amount": [100.0], "transaction_date": ["2024-01-15"]})

        result = service.match_payments(
            payments_made=payments,
            payment_confirmations=confirmations,
        )

        # Should return unmatched when columns missing
        assert len(result.matched_pairs) == 0


class TestFindPotentialMatches:
    """Tests for find_potential_matches method."""

    def test_finds_single_match(self):
        service = PaymentMatchingService()

        transaction = pd.Series({
            "amount": -100.0,
            "transaction_date": "2024-01-15",
        })
        candidates = pd.DataFrame({
            "amount": [100.0, 200.0],
            "transaction_date": ["2024-01-15", "2024-01-15"],
        })

        matches = service.find_potential_matches(
            transaction=transaction,
            candidates=candidates,
        )

        assert len(matches) == 1
        assert matches[0][0] == 0  # First candidate matches

    def test_returns_matches_by_confidence(self):
        service = PaymentMatchingService()

        transaction = pd.Series({
            "amount": -100.0,
            "transaction_date": "2024-01-15",
        })
        candidates = pd.DataFrame({
            "amount": [100.0, 100.0],
            "transaction_date": ["2024-01-18", "2024-01-15"],  # Different dates
        })

        matches = service.find_potential_matches(
            transaction=transaction,
            candidates=candidates,
        )

        assert len(matches) == 2
        # Closer date should have higher confidence
        assert matches[0][1] > matches[1][1]


class TestFactoryFunction:
    """Tests for create_payment_matcher factory."""

    def test_creates_service_with_defaults(self):
        service = create_payment_matcher()
        assert isinstance(service, PaymentMatchingService)

    def test_creates_service_with_custom_params(self):
        service = create_payment_matcher(max_days_apart=10, amount_tolerance=0.1)
        assert isinstance(service, PaymentMatchingService)


class TestRealWorldScenarios:
    """Tests simulating real payment reconciliation scenarios."""

    def test_credit_card_payment_cycle(self):
        """Simulate typical credit card payment flow."""
        service = PaymentMatchingService(max_days_apart=5)

        # Payments made from checking account
        payments = pd.DataFrame({
            "amount": [-500.0, -1200.0, -350.0],
            "transaction_date": ["2024-01-05", "2024-01-15", "2024-01-25"],
            "description": [
                "PAYMENT TO CHASE CARD",
                "CITI CARD ONLINE PAYMENT",
                "DISCOVER E-PAYMENT",
            ],
        })

        # Confirmations on credit cards
        confirmations = pd.DataFrame({
            "amount": [500.0, 1200.0, 350.0],
            "transaction_date": ["2024-01-06", "2024-01-17", "2024-01-26"],
            "description": [
                "ONLINE PAYMENT, THANK YOU",
                "AUTOPAY AUTO-PMT",
                "Payment Thank You-Mobile",
            ],
        })

        result = service.match_payments(
            payments_made=payments,
            payment_confirmations=confirmations,
        )

        assert len(result.matched_pairs) == 3
        assert result.is_fully_matched
        assert result.total_matched_amount == 2050.0

    def test_handles_unmatched_partial_payment(self):
        """Test when confirmation amount doesn't match payment."""
        service = PaymentMatchingService()

        payments = pd.DataFrame({
            "amount": [-1000.0],
            "transaction_date": ["2024-01-15"],
        })
        confirmations = pd.DataFrame({
            "amount": [500.0],  # Only partial payment confirmed
            "transaction_date": ["2024-01-16"],
        })

        result = service.match_payments(
            payments_made=payments,
            payment_confirmations=confirmations,
        )

        # Should not match due to amount difference
        assert len(result.matched_pairs) == 0
        assert not result.is_fully_matched

from __future__ import annotations

import pandas as pd

from budget_analyser.domain.category_mappers import CategoryMappers
from budget_analyser.domain.transaction_processing import TransactionProcessor


def test_rental_trip_maps_to_luxuries_not_needs() -> None:
    # Sub-category mapping contains a substring collision: "Rent" inside "Rental_trip".
    # Ensure we map exactly to the intended category (Luxuries) and not Needs.
    mappers = CategoryMappers(
        description_to_sub_category={
            "Rental_trip": ["SFO PARKING"],
        },
        sub_category_to_category={
            "Needs": ["Rent"],
            "Luxuries": ["Rental_trip"],
        },
    )

    processor = TransactionProcessor(mappers=mappers)

    df = pd.DataFrame(
        {
            "description": ["SFO PARKING"],
            "amount": [-120.0],
            "transaction_date": pd.to_datetime(["2025-01-15"]),
            "from_account": ["acc"],
        }
    )

    processed = processor.process(raw_transactions=df)

    assert list(processed["sub_category"]) == ["Rental_trip"]
    assert list(processed["category"]) == ["Luxuries"]
"""Mappers router for Budget Analyser API.

Provides endpoints for category mapping, sub-category mapping,
and cashflow classification.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from budget_analyser.api.dependencies import (
    get_mapper_controller,
    get_sub_category_mapper_controller,
    get_cashflow_mapper_controller,
    invalidate_reports,
)
from budget_analyser.features.mappers.mapper_controller import (
    MapperController,
)
from budget_analyser.features.mappers.sub_category_controller import (
    SubCategoryMapperController,
)
from budget_analyser.features.mappers.cashflow_controller import (
    CashflowMapperController,
)

router = APIRouter(prefix="/api/mappers", tags=["mappers"])


# ===================================================================
# Category Mapper (description -> sub-category)
# ===================================================================


@router.get("/unmapped")
def list_unmapped_transactions(
    *, controller: MapperController = Depends(get_mapper_controller),
) -> list[dict]:
    """List all unmapped transactions.

    Args:
        controller: Injected MapperController.

    Returns:
        List of unmapped transaction records.
    """
    df = controller.list_unmapped_transactions()
    if df.empty:
        return []
    # Convert dates to strings
    result = df.copy()
    for col in result.columns:
        if result[col].dtype == "datetime64[ns]":
            result[col] = result[col].dt.strftime("%Y-%m-%d")
    return result.to_dict(orient="records")


@router.get("/unmapped-descriptions")
def list_unmapped_descriptions(
    *, controller: MapperController = Depends(get_mapper_controller),
) -> list[str]:
    """List unique unmapped descriptions.

    Args:
        controller: Injected MapperController.

    Returns:
        List of unmapped description strings.
    """
    return controller.list_unmapped_descriptions()


@router.get("/sub-categories")
def list_sub_categories(
    *, controller: MapperController = Depends(get_mapper_controller),
) -> list[str]:
    """List all available sub-categories.

    Args:
        controller: Injected MapperController.

    Returns:
        List of sub-category strings.
    """
    return controller.list_sub_categories()


@router.get("/categories")
def list_categories(
    *, controller: MapperController = Depends(get_mapper_controller),
) -> list[str]:
    """List all available categories.

    Args:
        controller: Injected MapperController.

    Returns:
        List of category strings.
    """
    return controller.list_categories()


@router.post("/add-descriptions")
def add_descriptions_to_sub_category(
    *,
    sub_category: str,
    descriptions: list[str],
    controller: MapperController = Depends(get_mapper_controller),
) -> dict[str, str]:
    """Add transaction descriptions to a sub-category mapping.

    Args:
        sub_category: Target sub-category.
        descriptions: List of descriptions to add.
        controller: Injected MapperController.

    Returns:
        Success message.
    """
    for desc in descriptions:
        controller.add_description_to_sub_category(
            description=desc, sub_category=sub_category,
        )
    return {"message": f"Added {len(descriptions)} descriptions"}


@router.post("/create-sub-category")
def create_sub_category(
    *,
    sub_category: str,
    category: str,
    controller: MapperController = Depends(get_mapper_controller),
) -> dict[str, str]:
    """Create a new sub-category under a category.

    Args:
        sub_category: New sub-category name.
        category: Parent category name.
        controller: Injected MapperController.

    Returns:
        Success message.

    Raises:
        HTTPException: If creation fails.
    """
    try:
        controller.create_sub_category(
            sub_category=sub_category, category=category,
        )
        return {"message": f"Created sub-category '{sub_category}'"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/save")
def save_category_mappings(
    *, controller: MapperController = Depends(get_mapper_controller),
) -> dict[str, str]:
    """Save category mappings to disk and invalidate reports.

    Args:
        controller: Injected MapperController.

    Returns:
        Success message.
    """
    controller.save()
    invalidate_reports()
    return {"message": "Category mappings saved and reports regenerated"}


# ===================================================================
# Sub-Category Mapper (sub-category -> category)
# ===================================================================


@router.get("/sub-category-mapping")
def get_sub_category_mapping(
    *,
    controller: SubCategoryMapperController = Depends(
        get_sub_category_mapper_controller,
    ),
) -> dict[str, list[str]]:
    """Get the full sub-category to category mapping.

    Args:
        controller: Injected SubCategoryMapperController.

    Returns:
        Dict mapping category to list of sub-categories.
    """
    return controller.mapping()


@router.post("/sub-category-mapping")
def modify_sub_category_mapping(
    *,
    action: str,
    sub_category: str | None = None,
    category: str | None = None,
    sub_categories: list[str] | None = None,
    target_category: str | None = None,
    controller: SubCategoryMapperController = Depends(
        get_sub_category_mapper_controller,
    ),
) -> dict[str, str]:
    """Modify sub-category to category mappings.

    Args:
        action: "add" or "move".
        sub_category: Sub-category for "add" action.
        category: Category for "add" action.
        sub_categories: Sub-categories for "move" action.
        target_category: Target category for "move" action.
        controller: Injected SubCategoryMapperController.

    Returns:
        Success message.

    Raises:
        HTTPException: If action is invalid or parameters missing.
    """
    try:
        if action == "add":
            if not sub_category or not category:
                raise HTTPException(
                    status_code=400,
                    detail="sub_category and category required for 'add'",
                )
            controller.add_sub_category(
                sub_category=sub_category, category=category,
            )
            return {"message": f"Added '{sub_category}' to '{category}'"}

        if action == "move":
            if not sub_categories or not target_category:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "sub_categories and target_category required for 'move'"
                    ),
                )
            controller.move_sub_categories(
                sub_categories=sub_categories, target_category=target_category,
            )
            return {
                "message": (
                    f"Moved {len(sub_categories)} "
                    f"sub-categories to '{target_category}'"
                ),
            }

        raise HTTPException(
            status_code=400, detail=f"Invalid action: {action}",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/sub-category-mapping/save")
def save_sub_category_mapping(
    *,
    controller: SubCategoryMapperController = Depends(
        get_sub_category_mapper_controller,
    ),
) -> dict[str, str]:
    """Save sub-category mapping to disk.

    Args:
        controller: Injected SubCategoryMapperController.

    Returns:
        Success message.
    """
    controller.save()
    return {"message": "Sub-category mapping saved"}


# ===================================================================
# Cashflow Mapper (category -> earnings/expenses)
# ===================================================================


@router.get("/cashflow")
def get_cashflow_mapping(
    *,
    controller: CashflowMapperController = Depends(
        get_cashflow_mapper_controller,
    ),
) -> dict[str, list[str]]:
    """Get the full cashflow mapping (earnings/expenses -> categories).

    Args:
        controller: Injected CashflowMapperController.

    Returns:
        Dict with "earnings" and "expenses" lists.
    """
    return controller.mapping()


@router.post("/cashflow/add")
def add_category_to_cashflow(
    *,
    name: str,
    flow: str,
    controller: CashflowMapperController = Depends(
        get_cashflow_mapper_controller,
    ),
) -> dict[str, str]:
    """Add a category to earnings or expenses flow.

    Args:
        name: Category name.
        flow: "earnings" or "expenses".
        controller: Injected CashflowMapperController.

    Returns:
        Success message.

    Raises:
        HTTPException: If flow is invalid.
    """
    try:
        controller.add_category(name=name, flow=flow)
        return {"message": f"Added '{name}' to {flow}"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/cashflow/move")
def move_categories_in_cashflow(
    *,
    action: str,
    categories: list[str],
    controller: CashflowMapperController = Depends(
        get_cashflow_mapper_controller,
    ),
) -> dict[str, str]:
    """Move categories between earnings and expenses.

    Args:
        action: "to_earnings" or "to_expenses".
        categories: List of category names to move.
        controller: Injected CashflowMapperController.

    Returns:
        Success message.

    Raises:
        HTTPException: If action is invalid.
    """
    try:
        if action == "to_earnings":
            controller.move_to_earnings(categories=categories)
            return {
                "message": f"Moved {len(categories)} categories to earnings",
            }
        if action == "to_expenses":
            controller.move_to_expenses(categories=categories)
            return {
                "message": f"Moved {len(categories)} categories to expenses",
            }
        raise HTTPException(
            status_code=400, detail=f"Invalid action: {action}",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/cashflow/save")
def save_cashflow_mapping(
    *,
    controller: CashflowMapperController = Depends(
        get_cashflow_mapper_controller,
    ),
) -> dict[str, str]:
    """Save cashflow mapping to disk.

    Args:
        controller: Injected CashflowMapperController.

    Returns:
        Success message.
    """
    controller.save()
    return {"message": "Cashflow mapping saved"}

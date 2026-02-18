"""Net worth router for Budget Analyser API.

Provides endpoints for financial account management and net worth tracking.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from budget_analyser.api.dependencies import get_net_worth_controller
from budget_analyser.api.serializers import (
    AccountSchema,
    NetWorthSummarySchema,
    AddAccountRequest,
    UpdateBalanceRequest,
)
from budget_analyser.features.net_worth.service import NetWorthService

router = APIRouter(prefix="/api/net-worth", tags=["net-worth"])


@router.get("/accounts", response_model=list[AccountSchema])
def get_all_accounts(
    *, controller: NetWorthService = Depends(get_net_worth_controller),
) -> list[AccountSchema]:
    """List all financial accounts.

    Args:
        controller: Injected NetWorthService.

    Returns:
        List of AccountSchema.
    """
    accounts = controller.get_all_accounts()
    return [
        AccountSchema(
            id=a.id,
            name=a.name,
            account_type=a.account_type.value,
            balance=a.balance,
            last_updated=a.last_updated.strftime("%Y-%m-%d"),
            notes=a.notes,
        )
        for a in accounts
    ]


@router.post("/accounts")
def add_account(
    *,
    body: AddAccountRequest,
    controller: NetWorthService = Depends(get_net_worth_controller),
) -> dict[str, str]:
    """Add a new financial account.

    Args:
        body: AddAccountRequest with account details.
        controller: Injected NetWorthService.

    Returns:
        Success message.

    Raises:
        HTTPException: If account creation fails.
    """
    try:
        controller.add_account(
            name=body.name,
            account_type=body.account_type,
            balance=body.balance,
            notes=body.notes,
        )
        return {"message": "Account added successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.patch("/accounts/{account_id}/balance")
def update_account_balance(
    *,
    account_id: int,
    body: UpdateBalanceRequest,
    controller: NetWorthService = Depends(get_net_worth_controller),
) -> dict[str, str]:
    """Update the balance of an existing account.

    Args:
        account_id: Account ID.
        body: UpdateBalanceRequest with new balance.
        controller: Injected NetWorthService.

    Returns:
        Success message.

    Raises:
        HTTPException: If account not found.
    """
    try:
        controller.update_account_balance(
            account_id=account_id, balance=body.balance,
        )
        return {"message": "Account balance updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.delete("/accounts/{account_id}")
def delete_account(
    *,
    account_id: int,
    controller: NetWorthService = Depends(get_net_worth_controller),
) -> dict[str, str]:
    """Delete an account.

    Args:
        account_id: Account ID.
        controller: Injected NetWorthService.

    Returns:
        Success message.

    Raises:
        HTTPException: If account not found.
    """
    try:
        controller.delete_account(account_id=account_id)
        return {"message": "Account deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/summary", response_model=NetWorthSummarySchema)
def get_net_worth_summary(
    *, controller: NetWorthService = Depends(get_net_worth_controller),
) -> NetWorthSummarySchema:
    """Calculate net worth summary.

    Args:
        controller: Injected NetWorthService.

    Returns:
        NetWorthSummarySchema with totals and account details.
    """
    summary = controller.get_net_worth_summary()
    return NetWorthSummarySchema(
        total_assets=summary.total_assets,
        total_liabilities=summary.total_liabilities,
        net_worth=summary.net_worth,
        assets_by_type=summary.assets_by_type,
        liabilities_by_type=summary.liabilities_by_type,
        accounts=[
            AccountSchema(
                id=a.id,
                name=a.name,
                account_type=a.account_type.value,
                balance=a.balance,
                last_updated=a.last_updated.strftime("%Y-%m-%d"),
                notes=a.notes,
            )
            for a in summary.accounts
        ],
    )

"""Tests for path traversal validation in upload request serializers."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from budget_analyser.api.serializers import UploadRequest, ValidateRequest


class TestValidateRequestPathSafety:
    def test_absolute_path_is_accepted(self) -> None:
        req = ValidateRequest(
            file_path="/home/user/statements/citi.csv",
            bank_name="citi",
        )
        assert req.file_path == "/home/user/statements/citi.csv"

    def test_relative_path_is_rejected(self) -> None:
        with pytest.raises(ValidationError, match="absolute"):
            ValidateRequest(file_path="relative/citi.csv", bank_name="citi")

    def test_dotdot_traversal_is_rejected(self) -> None:
        with pytest.raises(ValidationError, match=r"\.\.|absolute"):
            ValidateRequest(
                file_path="/home/user/../../etc/passwd",
                bank_name="citi",
            )

    def test_dotdot_relative_traversal_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ValidateRequest(
                file_path="../sensitive.csv",
                bank_name="citi",
            )


class TestUploadRequestPathSafety:
    def test_absolute_path_is_accepted(self) -> None:
        req = UploadRequest(
            file_path="/Users/user/Downloads/discover.csv",
            bank_name="discover",
            account_type="credit",
        )
        assert req.file_path == "/Users/user/Downloads/discover.csv"

    def test_relative_path_is_rejected(self) -> None:
        with pytest.raises(ValidationError, match="absolute"):
            UploadRequest(
                file_path="discover.csv",
                bank_name="discover",
                account_type="credit",
            )

    def test_dotdot_traversal_is_rejected(self) -> None:
        with pytest.raises(ValidationError, match=r"\.\.|absolute"):
            UploadRequest(
                file_path="/home/user/../../../etc/creds.csv",
                bank_name="discover",
                account_type="credit",
            )

    def test_dotdot_only_path_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            UploadRequest(
                file_path="../../secret.csv",
                bank_name="citi",
                account_type="debit",
            )

"""Tests for path traversal validation in upload request serializers."""

from __future__ import annotations

import os
import sys

import pytest
from pydantic import ValidationError

from budget_analyser.api.serializers import UploadRequest, ValidateRequest

# Use a platform-appropriate absolute path for positive tests
_ABS_CSV = "C:\\Users\\user\\statements\\citi.csv" if sys.platform == "win32" \
    else "/home/user/statements/citi.csv"
_ABS_DISCOVER = "C:\\Users\\user\\Downloads\\discover.csv" if sys.platform == "win32" \
    else "/Users/user/Downloads/discover.csv"
_ABS_TRAVERSAL = "C:\\Users\\user\\..\\..\\etc\\passwd" if sys.platform == "win32" \
    else "/home/user/../../etc/passwd"
_ABS_TRAVERSAL2 = "C:\\Users\\user\\..\\..\\..\\etc\\creds.csv" if sys.platform == "win32" \
    else "/home/user/../../../etc/creds.csv"


class TestValidateRequestPathSafety:
    def test_absolute_path_is_accepted(self) -> None:
        req = ValidateRequest(
            file_path=_ABS_CSV,
            bank_name="citi",
        )
        assert req.file_path == _ABS_CSV

    def test_relative_path_is_rejected(self) -> None:
        with pytest.raises(ValidationError, match="absolute"):
            ValidateRequest(file_path="relative/citi.csv", bank_name="citi")

    def test_dotdot_traversal_is_rejected(self) -> None:
        with pytest.raises(ValidationError, match=r"\.\.|absolute"):
            ValidateRequest(
                file_path=_ABS_TRAVERSAL,
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
            file_path=_ABS_DISCOVER,
            bank_name="discover",
            account_type="credit",
        )
        assert req.file_path == _ABS_DISCOVER

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
                file_path=_ABS_TRAVERSAL2,
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

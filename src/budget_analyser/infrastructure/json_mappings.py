"""JSON mapping providers (infrastructure).

Purpose:
    Load keyword mappings used for transaction categorization.

Goal:
    Keep JSON parsing and filesystem access out of domain/presentation layers.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import logging
from budget_analyser.domain.errors import DataSourceError
from budget_analyser.domain.protocols import CategoryMappingProvider


def _load_json(path: Path) -> dict:
    """Load JSON content from a file.

    Args:
        path: Filesystem path to the JSON file.

    Returns:
        Parsed JSON data.

    Raises:
        DataSourceError: If the file does not exist or contains invalid JSON.
    """
    # Validate file existence before reading.
    if not path.exists():
        raise DataSourceError(f"JSON mapping file not found: {path}")
    # Read and parse with proper error handling.
    try:
        content = path.read_text(encoding="utf-8")
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise DataSourceError(
            f"Invalid JSON in mapping file {path}: {exc.msg} at line {exc.lineno}"
        ) from exc
    except UnicodeDecodeError as exc:
        raise DataSourceError(
            f"Encoding error reading mapping file {path}: {exc}"
        ) from exc
    except OSError as exc:
        raise DataSourceError(f"Error reading mapping file {path}: {exc}") from exc


@dataclass(frozen=True)
class JsonCategoryMappingProvider(CategoryMappingProvider):
    """JSON-backed category mapping provider.

    Example:
        >>> provider = JsonCategoryMappingProvider(
        ...     description_to_sub_category_path=Path("mappers/desc.json"),
        ...     sub_category_to_category_path=Path("mappers/sub.json"),
        ... )
        >>> mapping = provider.description_to_sub_category()
    """

    description_to_sub_category_path: Path
    sub_category_to_category_path: Path
    logger: logging.Logger | None = None

    def _log(self, level: int, msg: str, *args) -> None:
        log = self.logger or logging.getLogger("budget_analyser.gui")
        try:
            log.log(level, msg, *args)
        except Exception:  # pylint: disable=broad-exception-caught
            pass

    def description_to_sub_category(self) -> Mapping[str, list[str]]:
        """Load mapping from description keywords to sub-category labels.

        Returns:
            Mapping where keys are sub-category labels and values are
            lists of description keywords.

        Raises:
            DataSourceError: If the JSON file is missing or invalid.
        """
        path = self.description_to_sub_category_path
        mapping = _load_json(path)
        try:
            size = len(mapping or {})
            self._log(
                logging.DEBUG,
                "Loaded description->sub_category mapping: path=%s keys=%d",
                str(path),
                size,
            )
            if size == 0:
                self._log(logging.WARNING, "Mapping file is empty: %s", str(path))
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        return mapping

    def sub_category_to_category(self) -> Mapping[str, list[str]]:
        """Load mapping from sub-category keywords to category labels.

        Returns:
            Mapping where keys are category labels and values are
            lists of sub-category names.

        Raises:
            DataSourceError: If the JSON file is missing or invalid.
        """
        path = self.sub_category_to_category_path
        mapping = _load_json(path)
        try:
            size = len(mapping or {})
            self._log(
                logging.DEBUG,
                "Loaded sub_category->category mapping: path=%s keys=%d",
                str(path),
                size,
            )
            if size == 0:
                self._log(logging.WARNING, "Mapping file is empty: %s", str(path))
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        return mapping or {}


@dataclass(frozen=True)
class JsonCashflowMappingProvider:
    """JSON-backed provider for cashflow (earnings/expenses) mappings.

    Example:
        >>> provider = JsonCashflowMappingProvider(
        ...     cashflow_to_category_path=Path("mappers/cashflow.json"),
        ... )
        >>> mapping = provider.cashflow_to_category()
    """

    cashflow_to_category_path: Path
    logger: logging.Logger | None = None

    def _log(self, level: int, msg: str, *args) -> None:
        log = self.logger or logging.getLogger("budget_analyser.gui")
        try:
            log.log(level, msg, *args)
        except Exception:  # pylint: disable=broad-exception-caught
            pass

    def cashflow_to_category(self) -> Mapping[str, list[str]]:
        """Load mapping from cashflow type to category labels.

        Returns:
            Mapping where keys are cashflow types (e.g. "earnings",
            "expenses") and values are lists of category names.

        Raises:
            DataSourceError: If the JSON file is missing or invalid.
        """
        path = self.cashflow_to_category_path
        mapping = _load_json(path)
        try:
            size = len(mapping or {})
            self._log(
                logging.DEBUG,
                "Loaded cashflow->category mapping: path=%s keys=%d",
                str(path),
                size,
            )
            if size == 0:
                self._log(logging.WARNING, "Mapping file is empty: %s", str(path))
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        return mapping or {}


@dataclass
class JsonCategoryMappingStore:
    """Read/write store for category mapping JSON files.

    Responsibilities:
      - Provide mutable copies of the two mapping dicts.
      - Persist updates atomically (write to temp then replace).

    Notes:
      - Deduplication is caller's responsibility; this class writes what it receives.
    """

    description_to_sub_category_path: Path
    sub_category_to_category_path: Path
    logger: logging.Logger | None = None

    # ---- Loaders ----
    def load_desc_to_sub(self) -> dict[str, list[str]]:
        """Load the description-to-sub-category mapping from JSON.

        Returns:
            Mutable dict copy of the mapping file contents.

        Raises:
            DataSourceError: If the JSON file is missing or invalid.
        """
        return dict(_load_json(self.description_to_sub_category_path))

    def load_sub_to_cat(self) -> dict[str, list[str]]:
        """Load the sub-category-to-category mapping from JSON.

        Returns:
            Mutable dict copy of the mapping file contents.

        Raises:
            DataSourceError: If the JSON file is missing or invalid.
        """
        return dict(_load_json(self.sub_category_to_category_path))

    # ---- Savers ----
    def save_desc_to_sub(self, mapping: Mapping[str, list[str]]) -> None:
        """Persist the description-to-sub-category mapping to JSON.

        Args:
            mapping: The full mapping to write atomically.

        Raises:
            DataSourceError: If the file cannot be written.
        """
        self._atomic_write(self.description_to_sub_category_path, mapping)

    def save_sub_to_cat(self, mapping: Mapping[str, list[str]]) -> None:
        """Persist the sub-category-to-category mapping to JSON.

        Args:
            mapping: The full mapping to write atomically.

        Raises:
            DataSourceError: If the file cannot be written.
        """
        self._atomic_write(self.sub_category_to_category_path, mapping)

    # ---- Helpers ----
    def _atomic_write(self, path: Path, data: Mapping[str, list[str]]) -> None:
        try:
            tmp = path.with_suffix(path.suffix + ".tmp")
            path.parent.mkdir(parents=True, exist_ok=True)
            content = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False)
            tmp.write_text(content + "\n", encoding="utf-8")
            tmp.replace(path)
            if self.logger:
                try:
                    self.logger.info("Saved mapping: %s (size=%d)", str(path), len(data))
                except Exception:  # pylint: disable=broad-exception-caught
                    pass
        except Exception as exc:  # pragma: no cover - defensive
            raise DataSourceError(f"Failed to save mapping file: {path}: {exc}") from exc

    # Note: loading of sub_category->category for read-only use is provided by
    # JsonCategoryMappingProvider. The store focuses on read/write helpers above.


@dataclass
class JsonCashflowMappingStore:
    """Read/write store for cashflow (earnings/expenses) mapping JSON.

    Responsibilities:
      - Provide mutable copies of the cashflow mapping.
      - Persist updates atomically (write to temp then replace).
    """

    cashflow_to_category_path: Path
    logger: logging.Logger | None = None

    def load_cashflow(self) -> dict[str, list[str]]:
        """Load the cashflow-to-category mapping from JSON.

        Returns:
            Mutable dict copy of the mapping file contents.

        Raises:
            DataSourceError: If the JSON file is missing or invalid.
        """
        mapping = dict(_load_json(self.cashflow_to_category_path))
        # Normalize keys to preserve original casing order
        return mapping

    def save_cashflow(self, mapping: Mapping[str, list[str]]) -> None:
        """Persist the cashflow-to-category mapping to JSON.

        Args:
            mapping: The full mapping to write atomically.

        Raises:
            DataSourceError: If the file cannot be written.
        """
        self._atomic_write(self.cashflow_to_category_path, mapping)

    def _atomic_write(self, path: Path, data: Mapping[str, list[str]]) -> None:
        try:
            tmp = path.with_suffix(path.suffix + ".tmp")
            path.parent.mkdir(parents=True, exist_ok=True)
            content = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False)
            tmp.write_text(content + "\n", encoding="utf-8")
            tmp.replace(path)
            if self.logger:
                try:
                    self.logger.info("Saved cashflow mapping: %s (size=%d)", str(path), len(data))
                except Exception:  # pylint: disable=broad-exception-caught
                    pass
        except Exception as exc:  # pragma: no cover - defensive
            raise DataSourceError(f"Failed to save mapping file: {path}: {exc}") from exc

from __future__ import annotations

import configparser
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class IniAppConfig:
    path: Path

    def _parser(self) -> configparser.ConfigParser:
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(self.path, encoding="utf-8")
        return parser

    def list_accounts(self, *, section: str) -> list[str]:
        parser = self._parser()
        return list(parser.options(section))

    def get_statement_filename(self, *, section: str, account: str) -> str:
        parser = self._parser()
        return parser.get(section, account)

    def get_column_mapping(self, *, account_name: str) -> Mapping[str, str]:
        parser = self._parser()
        section = f"{account_name}_map"
        mapping_desired_to_source = dict(parser.items(section))
        return {source: desired for desired, source in mapping_desired_to_source.items()}

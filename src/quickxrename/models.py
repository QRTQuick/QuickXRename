from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PreviewEntry:
    item_type: str  # "file" or "folder"
    old_path: str
    raw_new_path: str
    final_new_path: str
    status: str  # "ready", "conflict", "invalid"
    message: str


@dataclass(frozen=True)
class PreviewStats:
    items: int
    ready: int
    conflicts: int
    invalid: int


@dataclass(frozen=True)
class RenameOperation:
    new_path: str
    old_path: str


@dataclass(frozen=True)
class PreviewRequest:
    directory: str
    recursive: bool
    include_files: bool
    include_folders: bool
    mode: str
    pattern: str
    replacement: str

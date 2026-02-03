from __future__ import annotations

import fnmatch
import os
import re
from typing import Iterable, List, Tuple

from .models import PreviewEntry, PreviewRequest, PreviewStats, RenameOperation


def is_invalid_name(name: str) -> str | None:
    if name == "":
        return "empty name"
    if os.sep in name or (os.altsep and os.altsep in name):
        return "path separator in name"
    if os.name == "nt":
        invalid = '<>:"/\\|?*'
        if any(ch in name for ch in invalid):
            return "invalid characters for Windows"
    return None


def compute_new_name(mode: str, pattern: str, replacement: str, name: str) -> str | None:
    if mode == "Replace":
        if not pattern:
            return None
        return name.replace(pattern, replacement)
    if mode == "Wildcard":
        if not pattern:
            return None
        if not fnmatch.fnmatch(name, pattern):
            return None
        if "*" in replacement:
            base, _ext = os.path.splitext(name)
            return replacement.replace("*", base)
        return replacement
    if mode == "Regex":
        if not pattern:
            return None
        try:
            return re.sub(pattern, replacement, name)
        except re.error:
            return None
    return None


def apply_folder_mapping(path: str, mappings: List[Tuple[str, str]]) -> str:
    # Apply deepest folders first for nested renames.
    updated = path
    for old_folder, new_folder in mappings:
        if updated == old_folder or updated.startswith(old_folder + os.sep):
            updated = new_folder + updated[len(old_folder):]
    return updated


def iter_items(directory: str, recursive: bool, include_files: bool, include_folders: bool) -> Iterable[Tuple[str, bool]]:
    if recursive:
        for root, dirs, files in os.walk(directory):
            if include_folders:
                for d in dirs:
                    yield os.path.join(root, d), True
            if include_files:
                for f in files:
                    yield os.path.join(root, f), False
    else:
        for entry in os.scandir(directory):
            if entry.is_dir() and include_folders:
                yield entry.path, True
            if entry.is_file() and include_files:
                yield entry.path, False


def build_preview(request: PreviewRequest, cancel_check) -> Tuple[List[PreviewEntry], PreviewStats]:
    entries: List[PreviewEntry] = []
    stats = PreviewStats(items=0, ready=0, conflicts=0, invalid=0)

    if not os.path.isdir(request.directory):
        return entries, stats

    items = list(iter_items(request.directory, request.recursive, request.include_files, request.include_folders))
    stats = PreviewStats(items=len(items), ready=0, conflicts=0, invalid=0)

    tentative: List[Tuple[str, str, bool]] = []
    for path, is_dir in items:
        if cancel_check():
            return [], stats
        name = os.path.basename(path)
        new_name = compute_new_name(request.mode, request.pattern, request.replacement, name)
        if new_name is None or new_name == name:
            continue
        invalid_reason = is_invalid_name(new_name)
        if invalid_reason:
            entries.append(PreviewEntry(
                item_type="folder" if is_dir else "file",
                old_path=path,
                raw_new_path=os.path.join(os.path.dirname(path), new_name),
                final_new_path=os.path.join(os.path.dirname(path), new_name),
                status="invalid",
                message=invalid_reason,
            ))
            stats = PreviewStats(stats.items, stats.ready, stats.conflicts, stats.invalid + 1)
            continue
        tentative.append((path, os.path.join(os.path.dirname(path), new_name), is_dir))

    folder_mappings = [(old_path, new_path) for old_path, new_path, is_dir in tentative if is_dir]
    folder_mappings.sort(key=lambda x: len(x[0]), reverse=True)

    source_paths = {p for p, _, _ in tentative}
    target_paths: dict[str, list[Tuple[str, bool]]] = {}

    for old_path, new_path, is_dir in tentative:
        final_new_path = apply_folder_mapping(new_path, folder_mappings)
        target_paths.setdefault(final_new_path, []).append((old_path, is_dir))

    for old_path, new_path, is_dir in tentative:
        if cancel_check():
            return [], stats
        final_new_path = apply_folder_mapping(new_path, folder_mappings)
        conflict = False
        message = ""

        if len(target_paths.get(final_new_path, [])) > 1:
            conflict = True
            message = "multiple items target same path"

        if os.path.exists(final_new_path) and final_new_path not in source_paths:
            conflict = True
            message = "target already exists"

        if conflict:
            entries.append(PreviewEntry(
                item_type="folder" if is_dir else "file",
                old_path=old_path,
                raw_new_path=new_path,
                final_new_path=final_new_path,
                status="conflict",
                message=message,
            ))
            stats = PreviewStats(stats.items, stats.ready, stats.conflicts + 1, stats.invalid)
        else:
            entries.append(PreviewEntry(
                item_type="folder" if is_dir else "file",
                old_path=old_path,
                raw_new_path=new_path,
                final_new_path=final_new_path,
                status="ready",
                message="",
            ))
            stats = PreviewStats(stats.items, stats.ready + 1, stats.conflicts, stats.invalid)

    return entries, stats


def apply_renames(entries: Iterable[PreviewEntry], log_fn) -> List[RenameOperation]:
    entries = list(entries)
    folder_renames = [(e.old_path, e.raw_new_path) for e in entries if e.item_type == "folder"]
    folder_renames.sort(key=lambda x: len(x[0]), reverse=True)

    operations: List[RenameOperation] = []

    for entry in [e for e in entries if e.item_type == "file"]:
        try:
            os.rename(entry.old_path, entry.raw_new_path)
            final_path = apply_folder_mapping(entry.raw_new_path, folder_renames)
            operations.append(RenameOperation(new_path=final_path, old_path=entry.old_path))
            log_fn(f"Renamed file: {entry.old_path} -> {final_path}")
        except OSError as exc:
            log_fn(f"Failed to rename file: {entry.old_path} -> {entry.raw_new_path} ({exc})")

    for entry in [e for e in entries if e.item_type == "folder"]:
        try:
            os.rename(entry.old_path, entry.raw_new_path)
            operations.append(RenameOperation(new_path=entry.final_new_path, old_path=entry.old_path))
            log_fn(f"Renamed folder: {entry.old_path} -> {entry.final_new_path}")
        except OSError as exc:
            log_fn(f"Failed to rename folder: {entry.old_path} -> {entry.raw_new_path} ({exc})")

    return operations


def undo_renames(operations: Iterable[RenameOperation], log_fn) -> None:
    for op in operations:
        try:
            if os.path.exists(op.new_path):
                os.rename(op.new_path, op.old_path)
                log_fn(f"Undo: {op.new_path} -> {op.old_path}")
            else:
                log_fn(f"Undo skipped (missing): {op.new_path}")
        except OSError as exc:
            log_fn(f"Undo failed: {op.new_path} -> {op.old_path} ({exc})")

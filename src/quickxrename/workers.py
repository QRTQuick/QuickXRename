from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QObject, QRunnable, Signal

from .models import PreviewEntry, PreviewRequest, PreviewStats, RenameOperation
from .renamer import apply_renames, build_preview


class WorkerSignals(QObject):
    progress = Signal(int, int)
    result = Signal(object)
    log = Signal(str)
    error = Signal(str)
    finished = Signal()


class PreviewTask(QRunnable):
    def __init__(self, request: PreviewRequest, cancel_flag: Callable[[], bool]):
        super().__init__()
        self.request = request
        self.cancel_flag = cancel_flag
        self.signals = WorkerSignals()

    def run(self) -> None:
        def cancel_check() -> bool:
            return self.cancel_flag()

        try:
            entries, stats = build_preview(self.request, cancel_check)
            self.signals.result.emit((entries, stats))
        except Exception as exc:  # noqa: BLE001
            self.signals.error.emit(str(exc))
        finally:
            self.signals.finished.emit()


class RenameTask(QRunnable):
    def __init__(self, entries: list[PreviewEntry]):
        super().__init__()
        self.entries = entries
        self.signals = WorkerSignals()

    def run(self) -> None:
        try:
            operations = apply_renames(self.entries, self.signals.log.emit)
            self.signals.result.emit(operations)
        except Exception as exc:  # noqa: BLE001
            self.signals.error.emit(str(exc))
        finally:
            self.signals.finished.emit()


class UndoTask(QRunnable):
    def __init__(self, operations: list[RenameOperation]):
        super().__init__()
        self.operations = operations
        self.signals = WorkerSignals()

    def run(self) -> None:
        from .renamer import undo_renames

        try:
            undo_renames(self.operations, self.signals.log.emit)
            self.signals.result.emit(True)
        except Exception as exc:  # noqa: BLE001
            self.signals.error.emit(str(exc))
        finally:
            self.signals.finished.emit()

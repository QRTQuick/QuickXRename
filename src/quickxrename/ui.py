from __future__ import annotations

from typing import List

from PySide6.QtCore import QTimer, Qt, QThreadPool
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QCheckBox,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QProgressBar,
)

from .models import PreviewEntry, PreviewRequest, PreviewStats, RenameOperation
from .workers import PreviewTask, RenameTask, UndoTask


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("QuickXRename")
        self.resize(1120, 740)

        self.thread_pool = QThreadPool.globalInstance()
        self.last_operations: List[RenameOperation] = []
        self._preview_entries: List[PreviewEntry] = []
        self._preview_token = 0

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(250)
        self._debounce.timeout.connect(self.refresh_preview)

        self._build_ui()

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)

        dir_row = QHBoxLayout()
        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText("Select a directory to rename")
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.pick_directory)
        dir_row.addWidget(QLabel("Directory"))
        dir_row.addWidget(self.dir_input)
        dir_row.addWidget(self.browse_btn)
        layout.addLayout(dir_row)

        options_row = QHBoxLayout()
        self.recursive_check = QCheckBox("Recursive")
        self.files_check = QCheckBox("Files")
        self.files_check.setChecked(True)
        self.folders_check = QCheckBox("Folders")
        self.folders_check.setChecked(True)
        options_row.addWidget(self.recursive_check)
        options_row.addWidget(self.files_check)
        options_row.addWidget(self.folders_check)
        options_row.addStretch(1)
        layout.addLayout(options_row)

        pattern_group = QGroupBox("Pattern")
        pattern_layout = QHBoxLayout(pattern_group)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Replace", "Wildcard", "Regex"])
        self.pattern_input = QLineEdit()
        self.pattern_input.setPlaceholderText("Pattern")
        self.replacement_input = QLineEdit()
        self.replacement_input.setPlaceholderText("Replacement")
        pattern_layout.addWidget(QLabel("Mode"))
        pattern_layout.addWidget(self.mode_combo)
        pattern_layout.addWidget(QLabel("Find"))
        pattern_layout.addWidget(self.pattern_input)
        pattern_layout.addWidget(QLabel("Replace"))
        pattern_layout.addWidget(self.replacement_input)
        layout.addWidget(pattern_group)

        action_row = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh Preview")
        self.refresh_btn.clicked.connect(self.refresh_preview)
        self.rename_btn = QPushButton("Rename")
        self.rename_btn.clicked.connect(self.perform_rename)
        self.undo_btn = QPushButton("Undo Last")
        self.undo_btn.clicked.connect(self.undo_last)
        self.rename_btn.setEnabled(False)
        self.undo_btn.setEnabled(False)
        action_row.addWidget(self.refresh_btn)
        action_row.addWidget(self.rename_btn)
        action_row.addWidget(self.undo_btn)
        action_row.addStretch(1)
        layout.addLayout(action_row)

        self.status_label = QLabel("Items: 0 | Ready: 0 | Conflicts: 0 | Invalid: 0")
        layout.addWidget(self.status_label)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Type", "Old Path", "New Path", "Status"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSortingEnabled(False)
        layout.addWidget(self.table, stretch=1)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("Applied changes will appear here")
        layout.addWidget(self.log_output)

        self.setCentralWidget(root)

        for widget in [
            self.dir_input,
            self.recursive_check,
            self.files_check,
            self.folders_check,
            self.mode_combo,
            self.pattern_input,
            self.replacement_input,
        ]:
            if isinstance(widget, QLineEdit):
                widget.textChanged.connect(self.schedule_preview)
            elif isinstance(widget, QCheckBox):
                widget.toggled.connect(self.schedule_preview)
            else:
                widget.currentIndexChanged.connect(self.schedule_preview)

    def log(self, message: str) -> None:
        self.log_output.append(message)

    def pick_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", "")
        if directory:
            self.dir_input.setText(directory)

    def schedule_preview(self) -> None:
        self._debounce.start()

    def refresh_preview(self) -> None:
        directory = self.dir_input.text().strip()
        if not directory:
            self._preview_entries = []
            self.table.setRowCount(0)
            self.rename_btn.setEnabled(False)
            return

        self._preview_token += 1
        token = self._preview_token

        request = PreviewRequest(
            directory=directory,
            recursive=self.recursive_check.isChecked(),
            include_files=self.files_check.isChecked(),
            include_folders=self.folders_check.isChecked(),
            mode=self.mode_combo.currentText(),
            pattern=self.pattern_input.text(),
            replacement=self.replacement_input.text(),
        )

        self.progress.setValue(10)
        self.rename_btn.setEnabled(False)

        task = PreviewTask(request, cancel_flag=lambda: token != self._preview_token)
        task.signals.result.connect(self.on_preview_ready)
        task.signals.error.connect(self.on_worker_error)
        task.signals.finished.connect(lambda: self.progress.setValue(100))
        self.thread_pool.start(task)

    def on_preview_ready(self, result) -> None:
        entries, stats = result
        self._preview_entries = entries
        self.table.setRowCount(0)

        ready = 0
        for entry in entries:
            row = self.table.rowCount()
            self.table.insertRow(row)

            type_item = QTableWidgetItem(entry.item_type)
            old_item = QTableWidgetItem(entry.old_path)
            new_item = QTableWidgetItem(entry.final_new_path)
            new_item.setData(Qt.UserRole, entry.raw_new_path)
            status_item = QTableWidgetItem(entry.status if not entry.message else f"{entry.status}: {entry.message}")

            if entry.status == "ready":
                color = QColor("#2d3a24")
                ready += 1
            elif entry.status == "conflict":
                color = QColor("#3a2022")
            else:
                color = QColor("#1f2533")

            for item in [type_item, old_item, new_item, status_item]:
                item.setBackground(color)

            self.table.setItem(row, 0, type_item)
            self.table.setItem(row, 1, old_item)
            self.table.setItem(row, 2, new_item)
            self.table.setItem(row, 3, status_item)

        self.table.resizeColumnsToContents()
        self._update_status(stats)
        self.rename_btn.setEnabled(ready > 0 and stats.conflicts == 0)
        self.progress.setValue(100)

    def _update_status(self, stats: PreviewStats) -> None:
        self.status_label.setText(
            f"Items: {stats.items} | Ready: {stats.ready} | Conflicts: {stats.conflicts} | Invalid: {stats.invalid}"
        )

    def _collect_ready_entries(self) -> List[PreviewEntry]:
        return [entry for entry in self._preview_entries if entry.status == "ready"]

    def perform_rename(self) -> None:
        entries = self._collect_ready_entries()
        if not entries:
            return

        self.rename_btn.setEnabled(False)
        self.progress.setValue(10)

        task = RenameTask(entries)
        task.signals.log.connect(self.log)
        task.signals.result.connect(self.on_rename_done)
        task.signals.error.connect(self.on_worker_error)
        task.signals.finished.connect(lambda: self.progress.setValue(100))
        self.thread_pool.start(task)

    def on_rename_done(self, operations: List[RenameOperation]) -> None:
        if operations:
            self.last_operations = operations
            self.undo_btn.setEnabled(True)
        self.refresh_preview()

    def undo_last(self) -> None:
        if not self.last_operations:
            return

        self.undo_btn.setEnabled(False)
        self.progress.setValue(10)

        task = UndoTask(self.last_operations)
        task.signals.log.connect(self.log)
        task.signals.error.connect(self.on_worker_error)
        task.signals.finished.connect(self.on_undo_done)
        self.thread_pool.start(task)

    def on_undo_done(self) -> None:
        self.last_operations = []
        self.progress.setValue(100)
        self.refresh_preview()

    def on_worker_error(self, message: str) -> None:
        if message:
            self.log(f"Error: {message}")

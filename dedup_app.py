#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Image‑duplicate finder – colourised UI
(without a separate refresh button – a new folder scan
auto‑refreshes the list)
"""

import sys, os, traceback
from pathlib import Path
from typing import Dict, List

# --------------------------------------------------------------
# Pillow / imagehash helpers
# --------------------------------------------------------------
from PIL import Image, ImageFile, UnidentifiedImageError
import imagehash

ImageFile.LOAD_TRUNCATED_IMAGES = True
ImageFile.MAX_IMAGE_PIXELS = None


def compute_hash(fp: Path) -> str:
    """Return the perceptual hash of *fp* or an empty string on error."""
    try:
        try:
            resample = Image.Resampling.LANCZOS
        except AttributeError:
            resample = Image.LANCZOS

        with Image.open(fp) as im:
            im = im.convert("L")
            im.thumbnail((512, 512), resample)
            return str(imagehash.phash(im))

    except UnidentifiedImageError:
        return ""
    except (OSError, PermissionError) as e:
        print(f"[hash-error] {fp} → {e}")
        return ""
    except Exception:
        print(f"[hash-error] {fp} → {traceback.format_exc()}")
        return ""


# --------------------------------------------------------------
# PyQt5 imports
# --------------------------------------------------------------
from PyQt5.QtCore import (
    Qt,
    QThread,
    pyqtSignal,
    pyqtSlot,
    QDir,
    QSize,
)
from PyQt5.QtGui import (
    QPixmap,
    QIcon,
    QBrush,
    QColor,
)
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QProgressDialog,
    QFileDialog,
    QMessageBox,
    QHeaderView,
    QCheckBox,
)

# --------------------------------------------------------------
# Colour map
# --------------------------------------------------------------
COLOUR_MAP = {
    "green": QColor("#ccffcc"),   # 1st duplicate
    "yellow": QColor("#ffffcc"),  # 2nd duplicate
    "orange": QColor("#ffd8b2"),  # 3rd duplicate
    "red": QColor("#ffcccc"),     # 4th duplicate
}


# --------------------------------------------------------------
# Background thread that scans for duplicates
# --------------------------------------------------------------
class ScanThread(QThread):
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(dict)

    def __init__(self, folder: Path):
        super().__init__()
        self.folder = folder

    def run(self):
        try:
            hash_map: Dict[str, List[Path]] = {}
            for file_path in self.folder.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in (
                    ".png", ".jpg", ".jpeg", ".gif", ".bmp"
                ):
                    h = compute_hash(file_path)
                    if h:
                        hash_map.setdefault(h, []).append(file_path)
            self.finished.emit({k: v for k, v in hash_map.items() if len(v) > 1})
        except Exception:
            print("[scan-thread] " + traceback.format_exc())
            self.finished.emit({})


# --------------------------------------------------------------
# Main application window
# --------------------------------------------------------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Deduplicator")
        self.resize(900, 700)
        self.setStyleSheet("background-color:#d3d3d3;")   # light‑gray

        self.folder: Path | None = None
        self.hash_map: Dict[str, List[Path]] = {}
        self.scan_thread: ScanThread | None = None

        # --- UI -----------------------------------
        self._build_ui()

    # --------------------------------------------------------------
    # UI construction
    # --------------------------------------------------------------
    def _build_ui(self):
        main_layout = QVBoxLayout()

        # --- colour check‑boxes -----------------------
        self.cb_green = QCheckBox("Green")
        self.cb_yellow = QCheckBox("Yellow")
        self.cb_orange = QCheckBox("Orange")
        self.cb_red = QCheckBox("Red")

        for cb in (self.cb_green, self.cb_yellow, self.cb_orange, self.cb_red):
            cb.stateChanged.connect(self._on_colour_changed)

        colour_box_layout = QHBoxLayout()
        colour_box_layout.addWidget(self.cb_green)
        colour_box_layout.addWidget(self.cb_yellow)
        colour_box_layout.addWidget(self.cb_orange)
        colour_box_layout.addWidget(self.cb_red)
        colour_box_layout.addStretch()

        # --- buttons --------------------------------
        btn_choose = QPushButton("Choose Folder")
        btn_choose.clicked.connect(self._choose_folder)

        self.btn_delete = QPushButton("Delete Selected")
        self.btn_delete.clicked.connect(self._delete_selected)
        self.btn_delete.setEnabled(False)

        button_layout = QHBoxLayout()
        button_layout.addWidget(btn_choose)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_delete)

        # --- tree ----------------------------------
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["", "Preview", "File", "Hash"])

        self.tree.header().setSectionResizeMode(
            0, QHeaderView.ResizeToContents   # checkbox column
        )
        self.tree.header().setSectionResizeMode(
            1, QHeaderView.ResizeToContents   # preview
        )
        self.tree.header().setSectionResizeMode(
            2, QHeaderView.Stretch           # full path
        )
        self.tree.header().setSectionResizeMode(
            3, QHeaderView.ResizeToContents   # hash
        )
        self.tree.setColumnWidth(0, 30)
        self.tree.setColumnWidth(1, 70)
        self.tree.setIconSize(QSize(64, 64))
        self.tree.itemChanged.connect(self._on_item_changed)

        # Assemble everything
        main_layout.addLayout(colour_box_layout)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.tree)
        self.setLayout(main_layout)

    # --------------------------------------------------------------
    # Folder selection & scan start
    # --------------------------------------------------------------
    def _choose_folder(self):
        chosen = QFileDialog.getExistingDirectory(
            self, "Select Image Folder", QDir.homePath()
        )
        if not chosen:
            return
        self.folder = Path(chosen)
        self._start_scan()

    def _reset_ui(self):
        """Clear tree, uncheck all colour boxes, and disable Delete."""
        self.tree.clear()
        self.cb_green.setChecked(False)
        self.cb_yellow.setChecked(False)
        self.cb_orange.setChecked(False)
        self.cb_red.setChecked(False)
        self.btn_delete.setEnabled(False)

    def _start_scan(self):
        if not self.folder:
            return

        # ---- reset UI before starting a new scan ----
        self._reset_ui()

        self.progress_dialog = QProgressDialog(
            "Scanning for duplicates…", "Abort", 0, 0, self
        )
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.canceled.connect(self._abort_scan)
        self.progress_dialog.show()

        # ---- launch background thread ----------------
        self.scan_thread = ScanThread(self.folder)
        self.scan_thread.progress.connect(self._on_progress)
        self.scan_thread.finished.connect(self._on_finished)
        self.scan_thread.start()

    def _abort_scan(self):
        if self.scan_thread:
            self.scan_thread.terminate()

    @pyqtSlot(int, int)
    def _on_progress(self, current, total):
        self.progress_dialog.setMaximum(total)
        self.progress_dialog.setValue(current)

    @pyqtSlot(dict)
    def _on_finished(self, hash_map):
        self.progress_dialog.hide()
        self.hash_map = hash_map
        self._populate_results()

    # --------------------------------------------------------------
    # Build tree from hash_map (colourise rows)
    # --------------------------------------------------------------
    def _populate_results(self):
        self.tree.clear()
        if not self.hash_map:
            QMessageBox.information(
                self, "No duplicates", "No duplicate images found."
            )
            return

        for h, paths in self.hash_map.items():
            group_item = QTreeWidgetItem(self.tree)
            group_item.setText(2, f"[{h}]  ({len(paths)} files)")
            group_item.setFirstColumnSpanned(True)

            for idx, fp in enumerate(paths):
                child = QTreeWidgetItem(group_item)

                # ----- make it checkable ------------------------------
                child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
                child.setCheckState(0, Qt.Unchecked)

                # ----- colour the row ------------------------------
                colour_name = list(COLOUR_MAP.keys())[idx] if idx < 4 else None
                if colour_name:
                    colour = COLOUR_MAP[colour_name]
                    for col in range(4):
                        child.setBackground(col, QBrush(colour))
                    child.setData(4, Qt.UserRole, colour_name)

                # ----- texts & icon ------------------------------------
                child.setText(1, "")          # preview column
                child.setText(2, str(fp))     # full path column
                child.setData(2, Qt.UserRole, fp)  # store Path object
                child.setText(3, h)           # hash column

                pix = QPixmap(str(fp))
                if pix.isNull():
                    pix = QPixmap(64, 64)
                    pix.fill(Qt.gray)
                else:
                    pix = pix.scaled(
                        64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                child.setIcon(1, QIcon(pix))

        self.tree.expandAll()
        self.btn_delete.setEnabled(False)

    # --------------------------------------------------------------
    # Delete selected items
    # --------------------------------------------------------------
    def _delete_selected(self):
        if not self.tree.topLevelItemCount():
            return

        to_delete: List[Path] = []
        for i in range(self.tree.topLevelItemCount()):
            group = self.tree.topLevelItem(i)
            for j in range(group.childCount()):
                child = group.child(j)
                if child.checkState(0) == Qt.Checked:
                    fp: Path = child.data(2, Qt.UserRole)
                    to_delete.append(fp)

        if not to_delete:
            QMessageBox.information(self, "Nothing selected", "No files checked.")
            return

        if not QMessageBox.question(
            self,
            "Confirm deletion",
            f"Delete {len(to_delete)} file(s)?",
            QMessageBox.Yes | QMessageBox.No,
        ):
            return

        for fp in to_delete:
            try:
                os.remove(fp)
            except Exception as e:
                print(f"[delete-error] {fp} → {e}")

        self._remove_deleted_paths(to_delete)
        self._populate_results()

    def _remove_deleted_paths(self, deleted: List[Path]):
        for h, paths in list(self.hash_map.items()):
            remaining = [p for p in paths if p not in deleted and p.exists()]
            if remaining:
                self.hash_map[h] = remaining
            else:
                del self.hash_map[h]

    # --------------------------------------------------------------
    # Colour check‑boxes → automatic selection/unselection
    # --------------------------------------------------------------
    def _on_colour_changed(self, state: int):
        """Select / unselect all items of a given colour."""
        sender = self.sender()
        colour_name = sender.text().lower()
        for i in range(self.tree.topLevelItemCount()):
            group = self.tree.topLevelItem(i)
            for j in range(group.childCount()):
                child = group.child(j)
                if child.data(4, Qt.UserRole) == colour_name:
                    child.setCheckState(0, Qt.Checked if state else Qt.Unchecked)

    # --------------------------------------------------------------
    # Update Delete button state
    # --------------------------------------------------------------
    def _on_item_changed(self, item: QTreeWidgetItem, column: int):
        if column == 0:
            any_checked = False
            for i in range(self.tree.topLevelItemCount()):
                group = self.tree.topLevelItem(i)
                for j in range(group.childCount()):
                    child = group.child(j)
                    if child.checkState(0) == Qt.Checked:
                        any_checked = True
                        break
                if any_checked:
                    break
            self.btn_delete.setEnabled(any_checked)


# --------------------------------------------------------------
# Application entry point
# --------------------------------------------------------------
def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QMessageBox, QFrame, QStyle, QApplication
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QSize

from Kernel.report_service import ReportService

BG = "#f5f7fb"; SURFACE = "#ffffff"; BORDER = "#e2e8f0"
TEXT = "#1e293b"; TEXT_MUTED = "#64748b"
PRIMARY = "#3b82f6"; PRIMARY_DK = "#2563eb"; PRIMARY_SOFT = "#dbeafe"


class ReportView(QWidget):
    def __init__(self, report_service: ReportService):
        super().__init__()
        self.report_service = report_service
        self.setStyleSheet(f"background-color: {BG};")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24); layout.setSpacing(20)

        header = QLabel("Reports")
        header.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {TEXT};")
        layout.addWidget(header)

        SP = QStyle.StandardPixmap
        layout.addWidget(self._create_report_card(
            "Inventory Report",
            "Export a CSV report of all products, current quantities, thresholds, and stock status.",
            "Export Inventory Report", SP.SP_FileDialogDetailedView, self._export_inventory))
        layout.addWidget(self._create_report_card(
            "Stock Movement Report",
            "Export a CSV report of all stock movements (IN and OUT) with dates and quantities.",
            "Export Movement Report", SP.SP_FileDialogContentsView, self._export_movements))
        layout.addStretch()

    def _create_report_card(self, title: str, description: str, button_text: str,
                            icon_sp, handler) -> QFrame:
        style = QApplication.instance().style()
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
        """)
        outer = QHBoxLayout(card)
        outer.setContentsMargins(20, 20, 20, 20); outer.setSpacing(16)

        # Icon chip
        chip = QFrame(); chip.setFixedSize(48, 48)
        chip.setStyleSheet(f"background-color: {PRIMARY_SOFT}; border: none; border-radius: 12px;")
        chip_lay = QVBoxLayout(chip); chip_lay.setContentsMargins(0, 0, 0, 0)
        chip_icon = QLabel()
        chip_icon.setPixmap(style.standardIcon(icon_sp).pixmap(QSize(22, 22)))
        chip_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chip_lay.addWidget(chip_icon)
        outer.addWidget(chip, 0, Qt.AlignmentFlag.AlignTop)

        # Text column
        text_col = QVBoxLayout(); text_col.setSpacing(4)
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {TEXT};")
        desc_label = QLabel(description)
        desc_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        desc_label.setWordWrap(True)
        text_col.addWidget(title_label); text_col.addWidget(desc_label)
        outer.addLayout(text_col, 1)

        # Button
        btn = QPushButton("  " + button_text)
        btn.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        btn.setIconSize(QSize(15, 15))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {PRIMARY}; color: white;
                border: none; border-radius: 8px;
                padding: 10px 18px; font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {PRIMARY_DK}; }}
        """)
        btn.clicked.connect(handler)
        outer.addWidget(btn, 0, Qt.AlignmentFlag.AlignVCenter)
        return card

    def _export_inventory(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Inventory Report",
                                                   "inventory_report.csv", "CSV Files (*.csv)")
        if not file_path: return
        try:
            self.report_service.export_inventory_report(file_path)
            QMessageBox.information(self, "Success", f"Inventory report exported to:\n{file_path}")
        except ValueError as e: QMessageBox.warning(self, "Export Failed", str(e))
        except Exception as e: QMessageBox.critical(self, "Error", f"Unexpected error: {e}")

    def _export_movements(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Movement Report",
                                                   "movement_report.csv", "CSV Files (*.csv)")
        if not file_path: return
        try:
            self.report_service.export_movement_report(file_path)
            QMessageBox.information(self, "Success", f"Movement report exported to:\n{file_path}")
        except ValueError as e: QMessageBox.warning(self, "Export Failed", str(e))
        except Exception as e: QMessageBox.critical(self, "Error", f"Unexpected error: {e}")

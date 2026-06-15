from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QMessageBox, QFrame
)
from PyQt6.QtGui import QFont

from Kernel.report_service import ReportService


class ReportView(QWidget):
    """Reports tab: export inventory and movement reports to CSV."""

    def __init__(self, report_service: ReportService):
        super().__init__()
        self.report_service = report_service
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        header = QLabel("Reports")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #ffffff;")
        layout.addWidget(header)

        # Inventory report card
        inventory_card = self._create_report_card(
            "Inventory Report",
            "Export a CSV report of all products, current quantities, thresholds, and stock status.",
            "Export Inventory Report",
            self._export_inventory
        )
        layout.addWidget(inventory_card)

        # Movement report card
        movement_card = self._create_report_card(
            "Stock Movement Report",
            "Export a CSV report of all stock movements (IN and OUT) with dates and quantities.",
            "Export Movement Report",
            self._export_movements
        )
        layout.addWidget(movement_card)

        layout.addStretch()

    def _create_report_card(self, title: str, description: str, button_text: str, handler) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #2a3142;
                border-radius: 10px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #ffffff;")

        desc_label = QLabel(description)
        desc_label.setStyleSheet("color: #9aa5b1; font-size: 12px;")
        desc_label.setWordWrap(True)

        btn = QPushButton(button_text)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border-radius: 6px;
                padding: 10px 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        btn.clicked.connect(handler)

        card_layout.addWidget(title_label)
        card_layout.addWidget(desc_label)
        card_layout.addWidget(btn)
        return card

    def _export_inventory(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Inventory Report", "inventory_report.csv", "CSV Files (*.csv)")
        if not file_path:
            return
        try:
            self.report_service.export_inventory_report(file_path)
            QMessageBox.information(self, "Success", f"Inventory report exported to:\n{file_path}")
        except ValueError as e:
            QMessageBox.warning(self, "Export Failed", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error: {e}")

    def _export_movements(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Movement Report", "movement_report.csv", "CSV Files (*.csv)")
        if not file_path:
            return
        try:
            self.report_service.export_movement_report(file_path)
            QMessageBox.information(self, "Success", f"Movement report exported to:\n{file_path}")
        except ValueError as e:
            QMessageBox.warning(self, "Export Failed", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error: {e}")
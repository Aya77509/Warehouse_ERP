from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QComboBox, QSpinBox, QLineEdit, QTabWidget
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from Kernel.product_service import ProductService
from Kernel.inventory_service import InventoryService


class StockMovementForm(QWidget):
    """Form for performing Stock IN or Stock OUT operations."""

    def __init__(self, movement_type: str, product_service: ProductService,
                 inventory_service: InventoryService, on_change_callback=None):
        super().__init__()
        self.movement_type = movement_type  # "IN" or "OUT"
        self.product_service = product_service
        self.inventory_service = inventory_service
        self.on_change_callback = on_change_callback
        self._build_ui()
        self.refresh_products()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        form_layout = QHBoxLayout()

        self.product_combo = QComboBox()
        self.product_combo.setMinimumWidth(220)
        self.product_combo.setStyleSheet(self._combo_style())

        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 1_000_000)
        self.quantity_input.setStyleSheet(self._combo_style())

        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("Note (optional)")
        self.note_input.setStyleSheet(self._combo_style())

        color = "#22c55e" if self.movement_type == "IN" else "#ef4444"
        action_btn = QPushButton(f"Stock {self.movement_type}")
        action_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
            }}
        """)
        action_btn.clicked.connect(self._perform_movement)

        label_style = "color: #e5e7eb; font-weight: bold;"

        product_label = QLabel("Product:")
        product_label.setStyleSheet(label_style)
        quantity_label = QLabel("Quantity:")
        quantity_label.setStyleSheet(label_style)

        form_layout.addWidget(product_label)
        form_layout.addWidget(self.product_combo)
        form_layout.addWidget(quantity_label)
        form_layout.addWidget(self.quantity_input)
        form_layout.addWidget(self.note_input)
        form_layout.addWidget(action_btn)

        layout.addLayout(form_layout)

        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #9aa5b1; font-size: 12px;")
        layout.addWidget(self.info_label)
        layout.addStretch()

        self.product_combo.currentIndexChanged.connect(self._update_info)

    @staticmethod
    def _combo_style() -> str:
        return """
            QComboBox, QSpinBox, QLineEdit {
                background-color: #2a3142;
                color: #ffffff;
                border: 1px solid #3a4256;
                border-radius: 6px;
                padding: 6px;
                font-size: 13px;
            }
        """

    def refresh_products(self):
        try:
            current_id = self.product_combo.currentData()
            self.product_combo.clear()
            for p in self.product_service.list_products():
                self.product_combo.addItem(f"{p.name} (ID: {p.id})", p.id)
            if current_id is not None:
                idx = self.product_combo.findData(current_id)
                if idx >= 0:
                    self.product_combo.setCurrentIndex(idx)
            self._update_info()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load products: {e}")

    def _update_info(self):
        product_id = self.product_combo.currentData()
        if product_id is None:
            self.info_label.setText("")
            return
        try:
            product = self.product_service.get_product(product_id)
            self.info_label.setText(
                f"Current stock: {product.quantity}  |  Low stock threshold: {product.low_stock_threshold}"
            )
        except ValueError:
            self.info_label.setText("")

    def _perform_movement(self):
        product_id = self.product_combo.currentData()
        if product_id is None:
            QMessageBox.information(self, "No Product", "No products available. Please add a product first.")
            return

        quantity = self.quantity_input.value()
        note = self.note_input.text()

        try:
            if self.movement_type == "IN":
                self.inventory_service.stock_in(product_id, quantity, note)
            else:
                self.inventory_service.stock_out(product_id, quantity, note)

            QMessageBox.information(self, "Success", f"Stock {self.movement_type} recorded successfully.")
            self.note_input.clear()
            self._update_info()
            if self.on_change_callback:
                self.on_change_callback()
        except ValueError as e:
            QMessageBox.warning(self, "Operation Failed", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error: {e}")


class HistoryTable(QWidget):
    """Displays the full stock movement history."""

    def __init__(self, inventory_service: InventoryService):
        super().__init__()
        self.inventory_service = inventory_service
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Date", "Product", "Type", "Quantity", "Note"])
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #2a3142;
                color: #e5e7eb;
                border: none;
                border-radius: 8px;
                gridline-color: #3a4256;
            }
            QHeaderView::section {
                background-color: #1e2530;
                color: #9aa5b1;
                padding: 6px;
                border: none;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 6px;
            }
        """)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

    def refresh(self):
        try:
            movements = self.inventory_service.get_history()
            self.table.setRowCount(0)
            for m in movements:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(m.date))
                self.table.setItem(row, 1, QTableWidgetItem(m.product_name))
                type_item = QTableWidgetItem(m.movement_type.value)
                type_item.setForeground(
                    Qt.GlobalColor.green if m.movement_type.value == "IN" else Qt.GlobalColor.red
                )
                self.table.setItem(row, 2, type_item)
                self.table.setItem(row, 3, QTableWidgetItem(str(m.quantity)))
                self.table.setItem(row, 4, QTableWidgetItem(m.note))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load history: {e}")


class InventoryView(QWidget):
    """Inventory tab: Stock IN, Stock OUT, and history sub-tabs."""

    def __init__(self, product_service: ProductService, inventory_service: InventoryService,
                 on_change_callback=None):
        super().__init__()
        self.product_service = product_service
        self.inventory_service = inventory_service
        self.on_change_callback = on_change_callback
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header = QLabel("Inventory Management")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #ffffff;")
        layout.addWidget(header)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: none; }
            QTabBar::tab {
                background-color: #2a3142;
                color: #9aa5b1;
                padding: 8px 16px;
                border-radius: 6px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background-color: #3b82f6;
                color: #ffffff;
            }
        """)

        self.stock_in_form = StockMovementForm(
            "IN", self.product_service, self.inventory_service, self._on_movement
        )
        self.stock_out_form = StockMovementForm(
            "OUT", self.product_service, self.inventory_service, self._on_movement
        )
        self.history_table = HistoryTable(self.inventory_service)

        self.tabs.addTab(self.stock_in_form, "Stock IN")
        self.tabs.addTab(self.stock_out_form, "Stock OUT")
        self.tabs.addTab(self.history_table, "Stock History")

        layout.addWidget(self.tabs)

    def _on_movement(self):
        self.history_table.refresh()
        self.stock_in_form.refresh_products()
        self.stock_out_form.refresh_products()
        if self.on_change_callback:
            self.on_change_callback()

    def refresh(self):
        self.stock_in_form.refresh_products()
        self.stock_out_form.refresh_products()
        self.history_table.refresh()
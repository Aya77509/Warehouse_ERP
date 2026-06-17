from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QComboBox,
    QSpinBox, QDialog, QFormLayout, QDialogButtonBox, QDateEdit, QCheckBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor

from Kernel.product_service import ProductService
from Kernel.supplier_service import SupplierService
from Kernel.entities import Product


class ProductDialog(QDialog):
    """Dialog for creating or editing a product."""

    def __init__(self, supplier_service: SupplierService, product: Product | None = None):
        super().__init__()
        self.supplier_service = supplier_service
        self.product = product
        self.setWindowTitle("Edit Product" if product else "Add Product")
        self.setMinimumWidth(360)
        self._build_ui()

    def _build_ui(self):
        layout = QFormLayout(self)

        self.name_input = QLineEdit()
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(0, 1_000_000)
        self.threshold_input = QSpinBox()
        self.threshold_input.setRange(0, 1_000_000)
        self.threshold_input.setValue(10)

        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem("None", None)
        for s in self.supplier_service.list_suppliers():
            self.supplier_combo.addItem(s.name, s.id)

        # Expiration date (optional)
        self.no_expiration_checkbox = QCheckBox("No expiration date")
        self.no_expiration_checkbox.setChecked(True)
        self.no_expiration_checkbox.stateChanged.connect(self._toggle_expiration_input)

        self.expiration_input = QDateEdit()
        self.expiration_input.setCalendarPopup(True)
        self.expiration_input.setDisplayFormat("yyyy-MM-dd")
        self.expiration_input.setDate(QDate.currentDate())
        self.expiration_input.setEnabled(False)

        if self.product:
            self.name_input.setText(self.product.name)
            self.quantity_input.setValue(self.product.quantity)
            self.threshold_input.setValue(self.product.low_stock_threshold)
            if self.product.supplier_id is not None:
                index = self.supplier_combo.findData(self.product.supplier_id)
                if index >= 0:
                    self.supplier_combo.setCurrentIndex(index)
            if self.product.expiration_date:
                self.no_expiration_checkbox.setChecked(False)
                qdate = QDate.fromString(self.product.expiration_date, "yyyy-MM-dd")
                if qdate.isValid():
                    self.expiration_input.setDate(qdate)

        layout.addRow("Name:", self.name_input)
        layout.addRow("Quantity:", self.quantity_input)
        layout.addRow("Low Stock Threshold:", self.threshold_input)
        layout.addRow("Supplier:", self.supplier_combo)
        layout.addRow("", self.no_expiration_checkbox)
        layout.addRow("Expiration Date:", self.expiration_input)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _toggle_expiration_input(self, state):
        self.expiration_input.setEnabled(not self.no_expiration_checkbox.isChecked())

    def get_data(self) -> dict:
        expiration_date = None
        if not self.no_expiration_checkbox.isChecked():
            expiration_date = self.expiration_input.date().toString("yyyy-MM-dd")
        return {
            "name": self.name_input.text(),
            "quantity": self.quantity_input.value(),
            "low_stock_threshold": self.threshold_input.value(),
            "supplier_id": self.supplier_combo.currentData(),
            "expiration_date": expiration_date
        }


class ProductView(QWidget):
    """Product management tab: list, search, add, edit, delete products."""

    def __init__(self, product_service: ProductService, supplier_service: SupplierService, on_change_callback=None):
        super().__init__()
        self.product_service = product_service
        self.supplier_service = supplier_service
        self.on_change_callback = on_change_callback
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header = QLabel("Product Management")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #ffffff;")
        layout.addWidget(header)

        # Toolbar
        toolbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search products by name...")
        self.search_input.setStyleSheet(self._input_style())
        self.search_input.textChanged.connect(self.refresh)

        add_btn = QPushButton("Add Product")
        add_btn.setStyleSheet(self._button_style("#22c55e"))
        add_btn.clicked.connect(self._add_product)

        edit_btn = QPushButton("Edit")
        edit_btn.setStyleSheet(self._button_style("#3b82f6"))
        edit_btn.clicked.connect(self._edit_product)

        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet(self._button_style("#ef4444"))
        delete_btn.clicked.connect(self._delete_product)

        toolbar.addWidget(self.search_input)
        toolbar.addStretch()
        toolbar.addWidget(add_btn)
        toolbar.addWidget(edit_btn)
        toolbar.addWidget(delete_btn)
        layout.addLayout(toolbar)

        # Table
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Quantity", "Low Stock Threshold", "Supplier", "Expiration"])
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
            QTableWidget::item:selected {
                background-color: #3b82f6;
            }
        """)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

    @staticmethod
    def _input_style() -> str:
        return """
            QLineEdit {
                background-color: #2a3142;
                color: #ffffff;
                border: 1px solid #3a4256;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #3b82f6;
            }
        """

    @staticmethod
    def _button_style(color: str) -> str:
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """

    def refresh(self):
        try:
            keyword = self.search_input.text()
            products = self.product_service.search_products(keyword)
            suppliers = {s.id: s.name for s in self.supplier_service.list_suppliers()}

            self.table.setRowCount(0)
            for p in products:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(p.id)))
                self.table.setItem(row, 1, QTableWidgetItem(p.name))

                qty_item = QTableWidgetItem(str(p.quantity))
                if p.is_low_stock():
                    qty_item.setForeground(Qt.GlobalColor.red)
                self.table.setItem(row, 2, qty_item)

                self.table.setItem(row, 3, QTableWidgetItem(str(p.low_stock_threshold)))
                supplier_name = suppliers.get(p.supplier_id, "—") if p.supplier_id else "—"
                self.table.setItem(row, 4, QTableWidgetItem(supplier_name))

                if p.expiration_date:
                    exp_item = QTableWidgetItem(p.expiration_date)
                    if p.is_expired():
                        exp_item.setForeground(QColor("#ef4444"))
                    elif p.is_expiring_soon():
                        exp_item.setForeground(QColor("#f59e0b"))
                else:
                    exp_item = QTableWidgetItem("—")
                self.table.setItem(row, 5, exp_item)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load products: {e}")

    def _get_selected_product_id(self) -> int | None:
        selected = self.table.currentRow()
        if selected < 0:
            return None
        return int(self.table.item(selected, 0).text())

    def _add_product(self):
        dialog = ProductDialog(self.supplier_service)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                self.product_service.create_product(**data)
                self.refresh()
                self._notify_change()
            except ValueError as e:
                QMessageBox.warning(self, "Validation Error", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add product: {e}")

    def _edit_product(self):
        product_id = self._get_selected_product_id()
        if product_id is None:
            QMessageBox.information(self, "No Selection", "Please select a product to edit.")
            return
        try:
            product = self.product_service.get_product(product_id)
            dialog = ProductDialog(self.supplier_service, product)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                data = dialog.get_data()
                product.name = data["name"]
                product.quantity = data["quantity"]
                product.low_stock_threshold = data["low_stock_threshold"]
                product.supplier_id = data["supplier_id"]
                product.expiration_date = data["expiration_date"]
                self.product_service.update_product(product)
                self.refresh()
                self._notify_change()
        except ValueError as e:
            QMessageBox.warning(self, "Validation Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to edit product: {e}")

    def _delete_product(self):
        product_id = self._get_selected_product_id()
        if product_id is None:
            QMessageBox.information(self, "No Selection", "Please select a product to delete.")
            return
        confirm = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete product ID {product_id}? This will also delete its movement history.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self.product_service.delete_product(product_id)
                self.refresh()
                self._notify_change()
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete product: {e}")

    def _notify_change(self):
        if self.on_change_callback:
            self.on_change_callback()
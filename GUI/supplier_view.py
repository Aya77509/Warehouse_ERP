from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QDialogButtonBox
)
from PyQt6.QtGui import QFont

from Kernel.supplier_service import SupplierService
from Kernel.entities import Supplier


class SupplierDialog(QDialog):
    """Dialog for creating or editing a supplier."""

    def __init__(self, supplier: Supplier | None = None):
        super().__init__()
        self.supplier = supplier
        self.setWindowTitle("Edit Supplier" if supplier else "Add Supplier")
        self.setMinimumWidth(360)
        self._build_ui()

    def _build_ui(self):
        layout = QFormLayout(self)

        self.name_input = QLineEdit()
        self.contact_input = QLineEdit()
        self.email_input = QLineEdit()
        self.address_input = QLineEdit()

        if self.supplier:
            self.name_input.setText(self.supplier.name)
            self.contact_input.setText(self.supplier.contact)
            self.email_input.setText(self.supplier.email)
            self.address_input.setText(self.supplier.address)

        layout.addRow("Name:", self.name_input)
        layout.addRow("Contact:", self.contact_input)
        layout.addRow("Email:", self.email_input)
        layout.addRow("Address:", self.address_input)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_data(self) -> dict:
        return {
            "name": self.name_input.text(),
            "contact": self.contact_input.text(),
            "email": self.email_input.text(),
            "address": self.address_input.text()
        }


class SupplierView(QWidget):
    """Supplier management tab: list, add, edit, delete suppliers."""

    def __init__(self, supplier_service: SupplierService, on_change_callback=None):
        super().__init__()
        self.supplier_service = supplier_service
        self.on_change_callback = on_change_callback
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header = QLabel("Supplier Management")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #ffffff;")
        layout.addWidget(header)

        toolbar = QHBoxLayout()
        add_btn = QPushButton("Add Supplier")
        add_btn.setStyleSheet(self._button_style("#22c55e"))
        add_btn.clicked.connect(self._add_supplier)

        edit_btn = QPushButton("Edit")
        edit_btn.setStyleSheet(self._button_style("#3b82f6"))
        edit_btn.clicked.connect(self._edit_supplier)

        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet(self._button_style("#ef4444"))
        delete_btn.clicked.connect(self._delete_supplier)

        view_products_btn = QPushButton("View Linked Products")
        view_products_btn.setStyleSheet(self._button_style("#8b5cf6"))
        view_products_btn.clicked.connect(self._view_linked_products)

        toolbar.addStretch()
        toolbar.addWidget(add_btn)
        toolbar.addWidget(edit_btn)
        toolbar.addWidget(delete_btn)
        toolbar.addWidget(view_products_btn)
        layout.addLayout(toolbar)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Contact", "Email"])
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
    def _button_style(color: str) -> str:
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }}
        """

    def refresh(self):
        try:
            suppliers = self.supplier_service.list_suppliers()
            self.table.setRowCount(0)
            for s in suppliers:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(s.id)))
                self.table.setItem(row, 1, QTableWidgetItem(s.name))
                self.table.setItem(row, 2, QTableWidgetItem(s.contact))
                self.table.setItem(row, 3, QTableWidgetItem(s.email))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load suppliers: {e}")

    def _get_selected_supplier_id(self) -> int | None:
        selected = self.table.currentRow()
        if selected < 0:
            return None
        return int(self.table.item(selected, 0).text())

    def _add_supplier(self):
        dialog = SupplierDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                self.supplier_service.create_supplier(**data)
                self.refresh()
                self._notify_change()
            except ValueError as e:
                QMessageBox.warning(self, "Validation Error", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add supplier: {e}")

    def _edit_supplier(self):
        supplier_id = self._get_selected_supplier_id()
        if supplier_id is None:
            QMessageBox.information(self, "No Selection", "Please select a supplier to edit.")
            return
        try:
            supplier = self.supplier_service.get_supplier(supplier_id)
            dialog = SupplierDialog(supplier)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                data = dialog.get_data()
                supplier.name = data["name"]
                supplier.contact = data["contact"]
                supplier.email = data["email"]
                supplier.address = data["address"]
                self.supplier_service.update_supplier(supplier)
                self.refresh()
                self._notify_change()
        except ValueError as e:
            QMessageBox.warning(self, "Validation Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to edit supplier: {e}")

    def _delete_supplier(self):
        supplier_id = self._get_selected_supplier_id()
        if supplier_id is None:
            QMessageBox.information(self, "No Selection", "Please select a supplier to delete.")
            return
        confirm = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete supplier ID {supplier_id}? Linked products will be unlinked.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self.supplier_service.delete_supplier(supplier_id)
                self.refresh()
                self._notify_change()
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete supplier: {e}")

    def _view_linked_products(self):
        supplier_id = self._get_selected_supplier_id()
        if supplier_id is None:
            QMessageBox.information(self, "No Selection", "Please select a supplier first.")
            return
        try:
            products = self.supplier_service.get_products_for_supplier(supplier_id)
            if not products:
                QMessageBox.information(self, "Linked Products", "No products are linked to this supplier.")
                return
            text = "\n".join(f"- {p.name} (Qty: {p.quantity})" for p in products)
            QMessageBox.information(self, "Linked Products", text)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load linked products: {e}")

    def _notify_change(self):
        if self.on_change_callback:
            self.on_change_callback()
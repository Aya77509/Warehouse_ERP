from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QMessageBox,
    QDialog, QFormLayout, QDialogButtonBox,
)

from Kernel.supplier_service import SupplierService
from Kernel.entities import Supplier

from GUI.theme import (
    BG, SURFACE, TEXT,
    Icons, primary_button, input_style, style_table, page_header,
)


class SupplierDialog(QDialog):
    def __init__(self, supplier: Supplier | None = None):
        super().__init__()
        self.supplier = supplier
        self.setWindowTitle("Edit Supplier" if supplier else "Add Supplier")
        self.setMinimumWidth(420)
        self.setStyleSheet(f"background-color: {SURFACE}; color: {TEXT}; {input_style()}")
        self._build_ui()

    def _build_ui(self):
        layout = QFormLayout(self)
        layout.setContentsMargins(20, 20, 20, 20); layout.setSpacing(12)
        self.name_input    = QLineEdit()
        self.contact_input = QLineEdit()
        self.email_input   = QLineEdit()
        self.address_input = QLineEdit()
        if self.supplier:
            self.name_input.setText(self.supplier.name)
            self.contact_input.setText(self.supplier.contact)
            self.email_input.setText(self.supplier.email)
            self.address_input.setText(self.supplier.address)
        layout.addRow("Name",    self.name_input)
        layout.addRow("Contact", self.contact_input)
        layout.addRow("Email",   self.email_input)
        layout.addRow("Address", self.address_input)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_data(self) -> dict:
        return {"name": self.name_input.text(), "contact": self.contact_input.text(),
                "email": self.email_input.text(), "address": self.address_input.text()}


class SupplierView(QWidget):
    def __init__(self, supplier_service: SupplierService, on_change_callback=None):
        super().__init__()
        self.supplier_service = supplier_service
        self.on_change_callback = on_change_callback
        self.setStyleSheet(f"background-color: {BG};")
        self._build_ui(); self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24); layout.setSpacing(18)
        layout.addWidget(page_header("Suppliers", "Manage supplier accounts and contacts"))

        toolbar = QHBoxLayout(); toolbar.setSpacing(10)
        add_btn  = primary_button("Add Supplier",         Icons.ADD,    "success")
        edit_btn = primary_button("Edit",                 Icons.EDIT,   "primary")
        del_btn  = primary_button("Delete",               Icons.DELETE, "danger")
        view_btn = primary_button("View Linked Products", Icons.VIEW,   "secondary")
        add_btn.clicked.connect(self._add_supplier)
        edit_btn.clicked.connect(self._edit_supplier)
        del_btn.clicked.connect(self._delete_supplier)
        view_btn.clicked.connect(self._view_linked_products)

        toolbar.addStretch()
        for b in (view_btn, add_btn, edit_btn, del_btn): toolbar.addWidget(b)
        layout.addLayout(toolbar)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Contact", "Email", "Address"])
        style_table(self.table)
        layout.addWidget(self.table)

    def refresh(self):
        try:
            suppliers = self.supplier_service.list_suppliers()
            self.table.setRowCount(0)
            for s in suppliers:
                row = self.table.rowCount(); self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(s.id)))
                self.table.setItem(row, 1, QTableWidgetItem(s.name))
                self.table.setItem(row, 2, QTableWidgetItem(s.contact))
                self.table.setItem(row, 3, QTableWidgetItem(s.email))
                self.table.setItem(row, 4, QTableWidgetItem(getattr(s, "address", "") or ""))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load suppliers: {e}")

    def _get_selected_supplier_id(self) -> int | None:
        sel = self.table.currentRow()
        if sel < 0: return None
        return int(self.table.item(sel, 0).text())

    def _add_supplier(self):
        dialog = SupplierDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                self.supplier_service.create_supplier(**data)
                self.refresh(); self._notify_change()
            except ValueError as e: QMessageBox.warning(self, "Validation Error", str(e))
            except Exception as e: QMessageBox.critical(self, "Error", f"Failed to add supplier: {e}")

    def _edit_supplier(self):
        sid = self._get_selected_supplier_id()
        if sid is None:
            QMessageBox.information(self, "No Selection", "Please select a supplier to edit."); return
        try:
            supplier = self.supplier_service.get_supplier(sid)
            dialog = SupplierDialog(supplier)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                data = dialog.get_data()
                supplier.name = data["name"]; supplier.contact = data["contact"]
                supplier.email = data["email"]; supplier.address = data["address"]
                self.supplier_service.update_supplier(supplier)
                self.refresh(); self._notify_change()
        except ValueError as e: QMessageBox.warning(self, "Validation Error", str(e))
        except Exception as e: QMessageBox.critical(self, "Error", f"Failed to edit supplier: {e}")

    def _delete_supplier(self):
        sid = self._get_selected_supplier_id()
        if sid is None:
            QMessageBox.information(self, "No Selection", "Please select a supplier to delete."); return
        confirm = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete supplier ID {sid}? Linked products will be unlinked.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self.supplier_service.delete_supplier(sid)
                self.refresh(); self._notify_change()
            except ValueError as e: QMessageBox.warning(self, "Error", str(e))
            except Exception as e: QMessageBox.critical(self, "Error", f"Failed to delete supplier: {e}")

    def _view_linked_products(self):
        sid = self._get_selected_supplier_id()
        if sid is None:
            QMessageBox.information(self, "No Selection", "Please select a supplier first."); return
        try:
            products = self.supplier_service.get_products_for_supplier(sid)
            if not products:
                QMessageBox.information(self, "Linked Products", "No products are linked to this supplier."); return
            text = "\n".join(f"• {p.name}  (Qty: {p.quantity})" for p in products)
            QMessageBox.information(self, "Linked Products", text)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load linked products: {e}")

    def _notify_change(self):
        if self.on_change_callback: self.on_change_callback()

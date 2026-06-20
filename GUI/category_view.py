from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QMessageBox,
    QDialog, QFormLayout, QDialogButtonBox,
)

from Kernel.category_service import CategoryService
from Kernel.entities import Category

from GUI.theme import (
    BG, SURFACE, TEXT,
    Icons, primary_button, input_style, style_table, page_header,
)


class CategoryDialog(QDialog):
    def __init__(self, category: Category | None = None):
        super().__init__()
        self.category = category
        self.setWindowTitle("Edit Category" if category else "Add Category")
        self.setMinimumWidth(380)
        self.setStyleSheet(f"background-color: {SURFACE}; color: {TEXT}; {input_style()}")
        self._build_ui()

    def _build_ui(self):
        layout = QFormLayout(self)
        layout.setContentsMargins(20, 20, 20, 20); layout.setSpacing(12)
        self.name_input = QLineEdit()
        if self.category:
            self.name_input.setText(self.category.name)
        layout.addRow("Name", self.name_input)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_data(self) -> dict:
        return {"name": self.name_input.text()}


class CategoryView(QWidget):
    def __init__(self, category_service: CategoryService, on_change_callback=None):
        super().__init__()
        self.category_service = category_service
        self.on_change_callback = on_change_callback
        self.setStyleSheet(f"background-color: {BG};")
        self._build_ui(); self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24); layout.setSpacing(18)
        layout.addWidget(page_header("Categories", "Organize products into categories"))

        toolbar = QHBoxLayout(); toolbar.setSpacing(10)
        add_btn  = primary_button("Add Category", Icons.ADD,    "success")
        edit_btn = primary_button("Edit",         Icons.EDIT,   "primary")
        del_btn  = primary_button("Delete",       Icons.DELETE, "danger")
        view_btn = primary_button("View Linked Products", Icons.VIEW, "secondary")
        add_btn.clicked.connect(self._add_category)
        edit_btn.clicked.connect(self._edit_category)
        del_btn.clicked.connect(self._delete_category)
        view_btn.clicked.connect(self._view_linked_products)

        toolbar.addStretch()
        for b in (view_btn, add_btn, edit_btn, del_btn): toolbar.addWidget(b)
        layout.addLayout(toolbar)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["ID", "Name"])
        style_table(self.table)
        layout.addWidget(self.table)

    def refresh(self):
        try:
            categories = self.category_service.list_categories()
            self.table.setRowCount(0)
            for c in categories:
                row = self.table.rowCount(); self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(c.id)))
                self.table.setItem(row, 1, QTableWidgetItem(c.name))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load categories: {e}")

    def _get_selected_category_id(self) -> int | None:
        sel = self.table.currentRow()
        if sel < 0: return None
        return int(self.table.item(sel, 0).text())

    def _add_category(self):
        dialog = CategoryDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                self.category_service.create_category(**data)
                self.refresh(); self._notify_change()
            except ValueError as e: QMessageBox.warning(self, "Validation Error", str(e))
            except Exception as e: QMessageBox.critical(self, "Error", f"Failed to add category: {e}")

    def _edit_category(self):
        cid = self._get_selected_category_id()
        if cid is None:
            QMessageBox.information(self, "No Selection", "Please select a category to edit."); return
        try:
            category = self.category_service.get_category(cid)
            dialog = CategoryDialog(category)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                data = dialog.get_data()
                category.name = data["name"]
                self.category_service.update_category(category)
                self.refresh(); self._notify_change()
        except ValueError as e: QMessageBox.warning(self, "Validation Error", str(e))
        except Exception as e: QMessageBox.critical(self, "Error", f"Failed to edit category: {e}")

    def _delete_category(self):
        cid = self._get_selected_category_id()
        if cid is None:
            QMessageBox.information(self, "No Selection", "Please select a category to delete."); return
        confirm = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete category ID {cid}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self.category_service.delete_category(cid)
                self.refresh(); self._notify_change()
            except ValueError as e: QMessageBox.warning(self, "Error", str(e))
            except Exception as e: QMessageBox.critical(self, "Error", f"Failed to delete category: {e}")

    def _view_linked_products(self):
        cid = self._get_selected_category_id()
        if cid is None:
            QMessageBox.information(self, "No Selection", "Please select a category first."); return
        try:
            products = self.category_service.get_products_for_category(cid)
            if not products:
                QMessageBox.information(self, "Linked Products", "No products are linked to this category."); return
            text = "\n".join(f"• {p.name}  (Qty: {p.quantity})" for p in products)
            QMessageBox.information(self, "Linked Products", text)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load linked products: {e}")

    def _notify_change(self):
        if self.on_change_callback: self.on_change_callback()

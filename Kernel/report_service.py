import csv

from Kernel.product_service import ProductService
from Kernel.inventory_service import InventoryService


class ReportService:
    """Business logic for generating exportable reports."""

    def __init__(self, product_service: ProductService, inventory_service: InventoryService):
        self.product_service = product_service
        self.inventory_service = inventory_service

    def export_inventory_report(self, file_path: str):
        products = self.product_service.list_products()
        try:
            with open(file_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Name", "Quantity", "Low Stock Threshold", "Supplier ID", "Status"])
                for p in products:
                    status = "LOW STOCK" if p.is_low_stock() else "OK"
                    writer.writerow([p.id, p.name, p.quantity, p.low_stock_threshold, p.supplier_id or "", status])
        except OSError as e:
            raise ValueError(f"Failed to export inventory report: {e}")

    def export_movement_report(self, file_path: str):
        movements = self.inventory_service.get_history()
        try:
            with open(file_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Date", "Product", "Type", "Quantity", "Note"])
                for m in movements:
                    writer.writerow([m.id, m.date, m.product_name, m.movement_type.value, m.quantity, m.note])
        except OSError as e:
            raise ValueError(f"Failed to export movement report: {e}")
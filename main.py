import sys
from PyQt6.QtWidgets import QApplication

from GUI.theme import global_stylesheet
from Infrastructure.database import Database
from Infrastructure.product_repository import ProductRepository
from Infrastructure.movement_repository import MovementRepository
from Infrastructure.supplier_repository import SupplierRepository
from Infrastructure.user_repository import UserRepository
from Kernel.auth_service import AuthService
from Kernel.product_service import ProductService
from Kernel.inventory_service import InventoryService
from Kernel.supplier_service import SupplierService
from Kernel.report_service import ReportService
from GUI.login_window import LoginWindow
from GUI.main_window import MainWindow


class Application:
    """Application bootstrapper: wires up infrastructure, kernel, and GUI layers."""

    def __init__(self):
        # Create QApplication FIRST, inside the class
        self.qt_app = QApplication(sys.argv)
        self.qt_app.setStyle("Fusion")
        self.qt_app.setStyleSheet(global_stylesheet())

        # Infrastructure layer
        self.db = Database()
        self.product_repo = ProductRepository(self.db)
        self.movement_repo = MovementRepository(self.db)
        self.supplier_repo = SupplierRepository(self.db)
        self.user_repo = UserRepository(self.db)

        # Kernel layer (business logic / services)
        self.auth_service = AuthService(self.user_repo)
        self.product_service = ProductService(self.product_repo)
        self.inventory_service = InventoryService(self.product_repo, self.movement_repo)
        self.supplier_service = SupplierService(self.supplier_repo, self.product_repo)
        self.report_service = ReportService(self.product_service, self.inventory_service)

        self.main_window = None
        self.login_window = None

    def run(self):
        self._show_login()
        sys.exit(self.qt_app.exec())

    def _show_login(self):
        self.login_window = LoginWindow(self.auth_service, self._on_login_success)
        self.login_window.show()

    def _on_login_success(self, user):
        self.login_window.close()
        self.main_window = MainWindow(
            user=user,
            product_service=self.product_service,
            inventory_service=self.inventory_service,
            supplier_service=self.supplier_service,
            report_service=self.report_service,
            on_logout_callback=self._show_login
        )
        self.main_window.show()


if __name__ == "__main__":
    app = Application()
    app.run()

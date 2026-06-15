from Infrastructure.supplier_repository import SupplierRepository
from Infrastructure.product_repository import ProductRepository
from Kernel.entities import Supplier


class SupplierService:
    """Business logic for supplier management."""

    def __init__(self, supplier_repo: SupplierRepository, product_repo: ProductRepository):
        self.supplier_repo = supplier_repo
        self.product_repo = product_repo

    def create_supplier(self, name: str, contact: str = "", email: str = "", address: str = "") -> Supplier:
        supplier = Supplier(id=None, name=name.strip(), contact=contact.strip(), email=email.strip(), address=address.strip())
        supplier.validate()
        supplier.id = self.supplier_repo.add(supplier)
        return supplier

    def update_supplier(self, supplier: Supplier):
        supplier.validate()
        if supplier.id is None:
            raise ValueError("Cannot update a supplier without an ID.")
        existing = self.supplier_repo.get_by_id(supplier.id)
        if existing is None:
            raise ValueError(f"Supplier with ID {supplier.id} does not exist.")
        self.supplier_repo.update(supplier)

    def delete_supplier(self, supplier_id: int):
        existing = self.supplier_repo.get_by_id(supplier_id)
        if existing is None:
            raise ValueError(f"Supplier with ID {supplier_id} does not exist.")
        # Unlink products from this supplier before deleting
        for product in self.product_repo.get_all():
            if product.supplier_id == supplier_id:
                product.supplier_id = None
                self.product_repo.update(product)
        self.supplier_repo.delete(supplier_id)

    def get_supplier(self, supplier_id: int) -> Supplier:
        supplier = self.supplier_repo.get_by_id(supplier_id)
        if supplier is None:
            raise ValueError(f"Supplier with ID {supplier_id} does not exist.")
        return supplier

    def list_suppliers(self) -> list[Supplier]:
        return self.supplier_repo.get_all()

    def get_products_for_supplier(self, supplier_id: int) -> list:
        return [p for p in self.product_repo.get_all() if p.supplier_id == supplier_id]
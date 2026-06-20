from Infrastructure.category_repository import CategoryRepository
from Infrastructure.product_repository import ProductRepository
from Kernel.entities import Category


class CategoryService:
    """Business logic for category management."""

    def __init__(self, category_repo: CategoryRepository, product_repo: ProductRepository):
        self.category_repo = category_repo
        self.product_repo = product_repo

    def create_category(self, name: str) -> Category:
        name = name.strip()
        category = Category(id=None, name=name)
        category.validate()
        if self.category_repo.name_exists(name):
            raise ValueError(f"A category named '{name}' already exists.")
        category.id = self.category_repo.add(category)
        return category

    def update_category(self, category: Category):
        category.name = category.name.strip()
        category.validate()
        if category.id is None:
            raise ValueError("Cannot update a category without an ID.")
        existing = self.category_repo.get_by_id(category.id)
        if existing is None:
            raise ValueError(f"Category with ID {category.id} does not exist.")
        if self.category_repo.name_exists(category.name, exclude_id=category.id):
            raise ValueError(f"A category named '{category.name}' already exists.")
        self.category_repo.update(category)

    def delete_category(self, category_id: int):
        existing = self.category_repo.get_by_id(category_id)
        if existing is None:
            raise ValueError(f"Category with ID {category_id} does not exist.")
        linked_products = self.product_repo.get_by_category(category_id)
        if linked_products:
            raise ValueError(
                f"Cannot delete category '{existing.name}': "
                f"{len(linked_products)} product(s) are still assigned to it. "
                f"Reassign or remove those products first."
            )
        self.category_repo.delete(category_id)

    def get_category(self, category_id: int) -> Category:
        category = self.category_repo.get_by_id(category_id)
        if category is None:
            raise ValueError(f"Category with ID {category_id} does not exist.")
        return category

    def list_categories(self) -> list[Category]:
        return self.category_repo.get_all()

    def get_products_for_category(self, category_id: int) -> list:
        return self.product_repo.get_by_category(category_id)

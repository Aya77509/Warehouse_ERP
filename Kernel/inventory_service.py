class InventoryService:


    @staticmethod
    def validate_stock_out(current_quantity, requested_quantity):

        if requested_quantity > current_quantity:
            return False

        return True



    @staticmethod
    def calculate_stock_after_movement(current, movement):

        return current + movement
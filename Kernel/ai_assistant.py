import ollama
from Kernel.product_service import ProductService
from Kernel.inventory_service import InventoryService
from Kernel.supplier_service import SupplierService
from Kernel.category_service import CategoryService


class AIAssistantService:
    """Service to interact with the local Ollama LLM for warehouse queries."""

    def __init__(
        self,
        product_service: ProductService,
        inventory_service: InventoryService,
        supplier_service: SupplierService,
        category_service: CategoryService,
        model: str = "llama3.2"
    ):
        self.product_service = product_service
        self.inventory_service = inventory_service
        self.supplier_service = supplier_service
        self.category_service = category_service
        self.model = model

    def _build_context(self) -> str:
        """Gathers data from services and builds a text-based context representation for the LLM."""
        # 1. Fetch categories
        try:
            categories = self.category_service.list_categories()
            cat_map = {c.id: c.name for c in categories}
        except Exception:
            cat_map = {}

        # 2. Fetch suppliers
        try:
            suppliers = self.supplier_service.list_suppliers()
            sup_map = {s.id: s.name for s in suppliers}
        except Exception:
            sup_map = {}

        # 3. Fetch products
        try:
            products = self.product_service.list_products()
        except Exception:
            products = []

        # 4. Fetch recent movements
        try:
            movements = self.inventory_service.get_recent_movements(15)
        except Exception:
            movements = []

        # Format context
        ctx = ["# WAREHOUSE CURRENT STATUS\n"]
        
        ctx.append("## Categories:")
        for cid, cname in cat_map.items():
            ctx.append(f"- ID {cid}: {cname}")
        ctx.append("")

        ctx.append("## Suppliers:")
        for sid, sname in sup_map.items():
            ctx.append(f"- ID {sid}: {sname}")
        ctx.append("")

        ctx.append("## Products in Inventory:")
        if not products:
            ctx.append("No products in the database.")
        for p in products:
            cat_name = cat_map.get(p.category_id, "None")
            sup_name = sup_map.get(p.supplier_id, "None")
            low_stock_status = "LOW STOCK!" if p.is_low_stock() else "OK"
            exp_status = f" (Expires: {p.expiration_date})" if p.expiration_date else ""
            ctx.append(
                f"- ID {p.id}: \"{p.name}\" | Qty: {p.quantity} (Threshold: {p.low_stock_threshold}) | "
                f"Price: ${p.price:.2f} | Category: {cat_name} | Supplier: {sup_name} | Status: {low_stock_status}{exp_status}"
            )
        ctx.append("")

        ctx.append("## Recent Stock Movements (last 15):")
        if not movements:
            ctx.append("No recent movements recorded.")
        for m in movements:
            ctx.append(f"- {m.date} | Product: \"{m.product_name}\" (ID: {m.product_id}) | Type: {m.movement_type.value} | Qty: {m.quantity} | Note: {m.note or 'N/A'}")

        return "\n".join(ctx)

    def query(self, user_message: str, chat_history: list[dict] = None) -> str:
        """Sends the user query along with warehouse context to Ollama and returns the response."""
        context = self._build_context()
        
        system_prompt = (
            "You are a helpful, concise AI Warehouse Assistant embedded in a Warehouse Management ERP app.\n"
            "You have access to the real-time warehouse data provided below. Use this data to answer the user's questions accurately.\n"
            "Keep your answers brief, professional, and clear. Avoid speculating or listing information not found in the context.\n"
            "If a user asks about stock, check the 'Products in Inventory' list.\n"
            "If a user asks about low stock, check which products have 'LOW STOCK!' status.\n"
            "If a user asks about recent movements, check the 'Recent Stock Movements' list.\n"
            "If the information is not in the context, politely state that you do not have that data.\n\n"
            f"{context}"
        )

        messages = [{"role": "system", "content": system_prompt}]
        
        # Add history if any
        if chat_history:
            messages.extend(chat_history)
            
        messages.append({"role": "user", "content": user_message})

        try:
            response = ollama.chat(model=self.model, messages=messages)
            return response["message"]["content"]
        except Exception as e:
            # Friendly error suggesting Ollama may not be running or model is missing
            return (
                f"⚠️ **Error connecting to local AI assistant:**\n\n"
                f"Could not reach Ollama using model `{self.model}`.\n\n"
                f"**Please verify:**\n"
                f"1. Ollama is running on your machine.\n"
                f"2. You have pulled the model by running:\n"
                f"   `ollama pull {self.model}`\n\n"
                f"*(Details: {str(e)})*"
            )

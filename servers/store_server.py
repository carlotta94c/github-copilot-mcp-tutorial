import json
import logging
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

logging.basicConfig(level=logging.WARNING, format="%(asctime)s - %(message)s")
logger = logging.getLogger("StoreMCP")
logger.setLevel(logging.INFO)

mcp = FastMCP("Bake & Take")

# In-memory product inventory: name -> {price, quantity}
INVENTORY = {
    "Pasticciotto": {"price": 2.50, "quantity": 40},
    "Rustico": {"price": 2.00, "quantity": 12},
    "Brioche": {"price": 2.25, "quantity": 20},
    "Krapfen": {"price": 3.00, "quantity": 35},
}


@mcp.resource("resource://inventory", mime_type="application/json")
async def get_inventory_data() -> str:
    """Read the full current inventory, including prices and stock levels."""
    return json.dumps(INVENTORY, indent=2)


@mcp.prompt
async def shopping_recommendation_prompt(
    preferences: Annotated[str, "Shopping preferences, occasion, or budget"] = "",
) -> str:
    """Generate shopping recommendations based on the current inventory."""
    inventory = await get_inventory_data()
    return f"""Please recommend products from the store using this current inventory:

{inventory}

Customer preferences: {preferences or "No specific preferences."}

Recommend only products with stock available and respect the available quantities.
Include suggested quantities, unit prices, and the total cost.
Explain how the recommendations fit the customer's preferences and any stated budget.
If no products match, explain why rather than inventing products or availability.
Provide recommendations only; do not purchase anything without explicit customer confirmation.
"""


@mcp.tool
async def list_products() -> dict:
    """List all available products with their prices and stock levels."""
    return INVENTORY


@mcp.tool
async def buy_product(
    name: Annotated[str, "Name of the product"],
    quantity: Annotated[int, "Quantity of product to buy"],
) -> str:
    """Buy a product from the store, reducing its inventory."""
    if name not in INVENTORY:
        raise ToolError(f"'{name}' is not available in the store.")
    product = INVENTORY[name]
    if product["quantity"] < quantity:
        raise ToolError(f"Only {product['quantity']} units of '{name}' are in stock.")
    product["quantity"] -= quantity
    total = product["price"] * quantity
    return f"Purchased {quantity}x {name} for ${total:.2f}. Remaining stock: {product['quantity']}."


if __name__ == "__main__":
    logger.info("Store MCP server starting (HTTP mode on port 8420)")
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8420)
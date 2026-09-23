from schemas import (
    SearchProductInput,
    CheckStockInput,
    BuyProductInput,
)

from tools import (
    search_product,
    check_stock,
    buy_product,
)


print("\n=== SEARCH ===")

result = search_product(
    SearchProductInput(query="laptop")
)

print(result)


print("\n=== STOCK ===")

result = check_stock(
    CheckStockInput(product_id=1)
)

print(result)


print("\n=== BUY ===")

result = buy_product(
    BuyProductInput(
        product_id=1,
        quantity=1,
    )
)

print(result)


print("\n=== STOCK AFTER PURCHASE ===")

result = check_stock(
    CheckStockInput(product_id=1)
)

print(result)
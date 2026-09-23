from schemas import (
    SearchProductInput,
    CheckStockInput,
    BuyProductInput,
)

from db import get_connection


def search_product(input_data: SearchProductInput) -> dict:
    query = input_data.query.strip().lower()

    if not query:
        return {
            "status": "error",
            "error_code": "INVALID_QUERY",
            "message": "Search query must not be empty.",
        }

    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, name, category, price
                FROM products
                WHERE
                    LOWER(name) LIKE %s
                    OR LOWER(category) LIKE %s
                ORDER BY price ASC
                """,
                (f"%{query}%", f"%{query}%"),
            )

            rows = cursor.fetchall()

        products = [
            {
                "id": row[0],
                "name": row[1],
                "category": row[2],
                "price": float(row[3]),
            }
            for row in rows
        ]

        return {
            "status": "success",
            "query": input_data.query,
            "products": products,
        }

    except Exception:
        return {
            "status": "error",
            "error_code": "SEARCH_FAILED",
            "message": "Product search failed.",
        }

    finally:
        conn.close()


def check_stock(input_data: CheckStockInput) -> dict:
    product_id = input_data.product_id

    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    p.id,
                    p.name,
                    i.stock
                FROM products p
                LEFT JOIN inventory i
                    ON i.product_id = p.id
                WHERE p.id = %s
                """,
                (product_id,),
            )

            row = cursor.fetchone()

        if row is None:
            return {
                "status": "error",
                "error_code": "PRODUCT_NOT_FOUND",
                "message": f"Product {product_id} was not found.",
            }

        stock = row[2] if row[2] is not None else 0

        return {
            "status": "success",
            "product_id": row[0],
            "product_name": row[1],
            "stock": stock,
            "in_stock": stock > 0,
        }

    except Exception:
        return {
            "status": "error",
            "error_code": "STOCK_CHECK_FAILED",
            "message": "Unable to check product stock.",
        }

    finally:
        conn.close()


def buy_product(input_data: BuyProductInput) -> dict:
    product_id = input_data.product_id
    quantity = input_data.quantity

    conn = get_connection()

    try:
        with conn:
            with conn.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        p.id,
                        p.name,
                        p.price,
                        i.stock
                    FROM products p
                    JOIN inventory i
                        ON i.product_id = p.id
                    WHERE p.id = %s
                    FOR UPDATE OF i
                    """,
                    (product_id,),
                )

                row = cursor.fetchone()

                if row is None:
                    return {
                        "status": "error",
                        "error_code": "PRODUCT_NOT_FOUND",
                        "message": "Product not found.",
                    }

                product_id = row[0]
                product_name = row[1]
                price = row[2]
                stock = row[3]

                if stock < quantity:
                    return {
                        "status": "error",
                        "error_code": "OUT_OF_STOCK",
                        "message": "Not enough stock available.",
                        "product_id": product_id,
                        "requested": quantity,
                        "available": stock,
                    }

                total_price = float(price) * quantity

                cursor.execute(
                    """
                    INSERT INTO purchases (
                        product_id,
                        quantity,
                        total_price
                    )
                    VALUES (%s, %s, %s)
                    RETURNING id, purchased_at
                    """,
                    (
                        product_id,
                        quantity,
                        total_price,
                    ),
                )

                purchase_id, purchased_at = cursor.fetchone()

                cursor.execute(
                    """
                    UPDATE inventory
                    SET stock = stock - %s
                    WHERE product_id = %s
                    """,
                    (
                        quantity,
                        product_id,
                    ),
                )

                remaining_stock = stock - quantity

                return {
                    "status": "success",
                    "message": "Purchase completed.",
                    "purchase_id": purchase_id,
                    "product_id": product_id,
                    "product_name": product_name,
                    "quantity": quantity,
                    "unit_price": float(price),
                    "total_price": total_price,
                    "remaining_stock": remaining_stock,
                    "purchased_at": str(purchased_at),
                }

    except Exception:
        return {
            "status": "error",
            "error_code": "BUY_EXECUTION_FAILED",
            "message": "Purchase failed safely. The transaction was rolled back.",
        }

    finally:
        conn.close()
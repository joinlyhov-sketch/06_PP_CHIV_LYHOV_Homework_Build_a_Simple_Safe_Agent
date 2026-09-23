-- Shopping Agent Database


-- ============================================


-- Products

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    price NUMERIC(10, 2) NOT NULL CHECK (price > 0)
);


-- Inventory

CREATE TABLE IF NOT EXISTS inventory (
    product_id INTEGER PRIMARY KEY,
    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),

    CONSTRAINT fk_inventory_product
        FOREIGN KEY (product_id)
        REFERENCES products(id)
        ON DELETE CASCADE
);


-- Purchases

CREATE TABLE IF NOT EXISTS purchases (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,

    quantity INTEGER NOT NULL
        CHECK (quantity > 0),

    total_price NUMERIC(10, 2) NOT NULL
        CHECK (total_price >= 0),

    purchased_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_purchase_product
        FOREIGN KEY (product_id)
        REFERENCES products(id)
);


-- Sample Products

INSERT INTO products (name, category, price)
VALUES
    ('Gaming Laptop', 'laptop', 999.99),
    ('Wireless Mouse', 'accessory', 29.99),
    ('Mechanical Keyboard', 'accessory', 79.99),
    ('USB-C Hub', 'accessory', 39.99)
ON CONFLICT DO NOTHING;



-- Inventory

INSERT INTO inventory (product_id, stock)
SELECT id, 5
FROM products
WHERE name = 'Gaming Laptop'
ON CONFLICT (product_id) DO NOTHING;


INSERT INTO inventory (product_id, stock)
SELECT id, 10
FROM products
WHERE name = 'Wireless Mouse'
ON CONFLICT (product_id) DO NOTHING;


INSERT INTO inventory (product_id, stock)
SELECT id, 0
FROM products
WHERE name = 'Mechanical Keyboard'
ON CONFLICT (product_id) DO NOTHING;


INSERT INTO inventory (product_id, stock)
SELECT id, 7
FROM products
WHERE name = 'USB-C Hub'
ON CONFLICT (product_id) DO NOTHING;
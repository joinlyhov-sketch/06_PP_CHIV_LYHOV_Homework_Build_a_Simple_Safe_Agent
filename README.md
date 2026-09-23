# Shopping Agent

A small autonomous shopping agent built with **Python, Ollama, PostgreSQL, and Pydantic**.

The agent uses a local LLM (`llama3.2:latest`) to understand a user's shopping request and decide when to call tools.

The project demonstrates a basic **Agent Loop**:

```text
User Request
     ↓
    LLM
     ↓
Tool Decision
     ↓
Harness
     ↓
Permission + Input Validation + Safety Check
     ↓
Tool Execution
     ↓
PostgreSQL
     ↓
Tool Result
     ↓
    LLM
     ↓
Next Decision
     ↓
Final Answer
```

The project intentionally keeps the scope small and focuses on the required agent concepts:

- Tool calling
- Structured tool inputs
- Tool execution
- Permission control
- Input validation
- Error handling
- Maximum tool-call limit
- PostgreSQL database integration

---

# 1. Project Overview

The **Shopping Agent** is a simple AI agent that helps users interact with a small product database.

The agent can:

1. Search for products.
2. Check product stock.
3. Purchase a product when the user has permission.

The LLM does not directly access the database.

Instead, the LLM requests a tool call, and the application controls whether that tool is allowed to execute.

### Example

A user might ask:

```text
Find me a laptop and buy one if it is in stock.
```

The agent can decide to perform:

```text
search_product
      ↓
check_stock
      ↓
buy_product
      ↓
final answer
```

The important concept is that the **LLM decides what action may be useful, but the application controls whether that action is actually executed.**

---

# 2. Available Tools

The Shopping Agent provides three tools.

## 2.1 `search_product`

Searches the PostgreSQL product database by product name or category.

### Input

```json
{
  "query": "laptop"
}
```

### Example result

```json
{
  "status": "success",
  "query": "laptop",
  "products": [
    {
      "id": 1,
      "name": "Gaming Laptop",
      "category": "laptop",
      "price": 999.99
    }
  ]
}
```

---

## 2.2 `check_stock`

Checks the current inventory of a specific product.

### Input

```json
{
  "product_id": 1
}
```

### Example result

```json
{
  "status": "success",
  "product_id": 1,
  "product_name": "Gaming Laptop",
  "stock": 5,
  "in_stock": true
}
```

---

## 2.3 `buy_product`

Purchases a product if enough inventory is available.

### Input

```json
{
  "product_id": 1,
  "quantity": 1
}
```

The quantity must be:

```text
1 <= quantity <= 2
```

The purchase performs two database operations inside one transaction:

```text
Create purchase
      +
Decrease inventory
```

If the operation fails, the transaction is rolled back.

### Example result

```json
{
  "status": "success",
  "message": "Purchase completed.",
  "purchase_id": 1,
  "product_id": 1,
  "product_name": "Gaming Laptop",
  "quantity": 1,
  "unit_price": 999.99,
  "total_price": 999.99,
  "remaining_stock": 4
}
```

---

# 3. Agent Loop

The agent follows a simple autonomous tool-calling loop.

```text
                ┌─────────────────┐
                │   User Request  │
                └────────┬────────┘
                         ↓
                ┌─────────────────┐
                │   Ollama LLM    │
                │ llama3.2:latest │
                └────────┬────────┘
                         ↓
                  Tool Decision
                         ↓
                ┌─────────────────┐
                │    Harness      │
                │                 │
                │ Permission      │
                │ Validation      │
                │ Call Limit      │
                └────────┬────────┘
                         ↓
                  Tool Execution
                         ↓
                ┌─────────────────┐
                │   PostgreSQL    │
                └────────┬────────┘
                         ↓
                   Tool Result
                         ↓
                ┌─────────────────┐
                │   Ollama LLM    │
                └────────┬────────┘
                         ↓
                  Need another
                     action?
                    /       \
                  Yes        No
                   ↓          ↓
              Tool Call   Final Answer
                   |
                   └──────→ LLM
```

The basic loop is:

```text
User Request
     ↓
LLM Decision
     ↓
Tool Call
     ↓
Harness Authorization
     ↓
Tool Execution
     ↓
Tool Result
     ↓
LLM Observation
     ↓
Next Decision
     ↓
Final Answer
```

For example:

```text
User:
"Find me a laptop and buy one if it is in stock."

        ↓

LLM:
search_product("laptop")

        ↓

PostgreSQL:
Gaming Laptop — ID 1 — $999.99

        ↓

LLM:
check_stock(product_id=1)

        ↓

PostgreSQL:
Stock = 5

        ↓

LLM:
buy_product(product_id=1, quantity=1)

        ↓

PostgreSQL:
Purchase successful

        ↓

LLM:
Final answer
```

---

# 4. Permission Rule

The application uses two roles:

- `customer`
- `admin`

Permissions are enforced by `harness.py`.

The LLM cannot bypass these permissions simply by requesting a tool.

| Role     | `search_product` | `check_stock` | `buy_product` |
| -------- | ---------------: | ------------: | ------------: |
| customer |              Yes |           Yes |            No |
| admin    |              Yes |           Yes |           Yes |

### Customer

A customer can:

```text
search_product
check_stock
```

A customer cannot:

```text
buy_product
```

If a customer attempts to purchase something, the harness returns:

```json
{
  "status": "error",
  "error_code": "PERMISSION_DENIED",
  "message": "Role 'customer' is not allowed to execute 'buy_product'."
}
```

The `buy_product()` function is not executed.

### Admin

An admin can use all three tools:

```text
search_product
check_stock
buy_product
```

This demonstrates that **permission control is implemented in application code rather than relying only on the LLM prompt.**

---

# 5. Safety

The project includes several basic safety mechanisms required for the agent.

## 5.1 Input Validation

Tool inputs are validated using **Pydantic** schemas.

For example:

```python
class CheckStockInput(BaseModel):
    product_id: int = Field(
        ...,
        gt=0
    )
```

Therefore:

```text
product_id = 1
```

is valid.

But:

```text
product_id = -1
```

is rejected.

The purchase quantity also has a boundary:

```python
quantity: int = Field(
    ...,
    gt=0,
    le=2
)
```

Therefore the allowed quantity is:

```text
1 or 2
```

This prevents invalid values from reaching the database tool.

---

## 5.2 Permission Validation

Every tool request passes through the harness before execution.

```text
LLM requests tool
       ↓
authorize_tool_call()
       ↓
Check role
       ↓
Check permission
       ↓
Validate input
       ↓
Execute tool
```

The LLM does not directly call the database functions.

---

## 5.3 Controlled Error Handling

Tools return structured error responses instead of exposing uncontrolled exceptions.

Examples:

```text
PRODUCT_NOT_FOUND
OUT_OF_STOCK
INVALID_INPUT
PERMISSION_DENIED
SEARCH_FAILED
STOCK_CHECK_FAILED
BUY_EXECUTION_FAILED
```

Example:

```json
{
  "status": "error",
  "error_code": "OUT_OF_STOCK",
  "message": "Not enough stock available.",
  "product_id": 3,
  "requested": 1,
  "available": 0
}
```

---

## 5.4 Database Transaction Safety

`buy_product` uses a PostgreSQL transaction.

The purchase and inventory update are performed together:

```text
BEGIN
   ↓
Check product + stock
   ↓
Create purchase
   ↓
Decrease inventory
   ↓
COMMIT
```

If an error occurs:

```text
ROLLBACK
```

This prevents a situation where the purchase is recorded but the inventory update fails.

---

## 5.5 Maximum Tool-Call Limit

The agent has a maximum of:

```text
5 tool calls
```

This prevents the agent from continuing indefinitely.

The flow is:

```text
Tool call 1
     ↓
Tool call 2
     ↓
Tool call 3
     ↓
Tool call 4
     ↓
Tool call 5
     ↓
STOP
```

If the limit is reached, the agent stops safely.

---

# 6. Example Run

The following is an example of the intended agent interaction.

## Example: Admin Purchase

Start the program:

```bash
python main.py
```

The program asks for a role:

```text
============================================================
SHOPPING AGENT
============================================================

Available roles:
1. customer
2. admin

Enter role [customer/admin]: admin
```

Then enter:

```text
Find me a laptop and buy one if it is in stock.
```

The agent may perform the following tool calls:

```text
============================================================
AGENT THINKING / DECISION
============================================================

TOOL REQUEST
------------------------------------------------------------
Tool: search_product
Arguments: {'query': 'laptop'}
Tool call: 1/5

TOOL RESULT
------------------------------------------------------------
{
  "status": "success",
  "query": "laptop",
  "products": [
    {
      "id": 1,
      "name": "Gaming Laptop",
      "category": "laptop",
      "price": 999.99
    }
  ]
}
```

The LLM observes the result and decides to check stock:

```text
============================================================
AGENT THINKING / DECISION
============================================================

TOOL REQUEST
------------------------------------------------------------
Tool: check_stock
Arguments: {'product_id': 1}
Tool call: 2/5

TOOL RESULT
------------------------------------------------------------
{
  "status": "success",
  "product_id": 1,
  "product_name": "Gaming Laptop",
  "stock": 5,
  "in_stock": true
}
```

The LLM then requests the purchase:

```text
============================================================
AGENT THINKING / DECISION
============================================================

TOOL REQUEST
------------------------------------------------------------
Tool: buy_product
Arguments: {'product_id': 1, 'quantity': 1}
Tool call: 3/5

TOOL RESULT
------------------------------------------------------------
{
  "status": "success",
  "message": "Purchase completed.",
  "purchase_id": 1,
  "product_id": 1,
  "product_name": "Gaming Laptop",
  "quantity": 1,
  "unit_price": 999.99,
  "total_price": 999.99,
  "remaining_stock": 4
}
```

Finally, the LLM provides the final answer:

```text
============================================================
FINAL ANSWER
============================================================

The Gaming Laptop was successfully purchased.
Quantity: 1
Total price: $999.99
Remaining stock: 4
```

---

# Project Structure

```text
shopping-agent/
│
├── README.md
├── main.py
├── agent.py
├── tools.py
├── schemas.py
├── harness.py
├── db.py
├── schema.sql
├── .env
└── .gitignore
```

### File Responsibilities

| File         | Purpose                                               |
| ------------ | ----------------------------------------------------- |
| `main.py`    | Starts the application and gets user input            |
| `agent.py`   | Implements the LLM agent loop and tool calling        |
| `tools.py`   | Implements the three shopping tools                   |
| `schemas.py` | Defines Pydantic input schemas                        |
| `harness.py` | Handles permissions, validation, and tool-call limits |
| `db.py`      | Creates PostgreSQL connections                        |
| `schema.sql` | Creates and initializes the database                  |
| `.env`       | Stores local database configuration                   |
| `README.md`  | Project documentation                                 |

---

# Requirements

Before running the project, install the following:

## 1. Python

Python **3.11 or newer** is recommended.

Check your version:

```bash
python --version
```

Example:

```text
Python 3.11.9
```

---

## 2. PostgreSQL

PostgreSQL must be installed and running.

Check:

```bash
psql --version
```

The project uses PostgreSQL for:

```text
products
inventory
purchases
```

---

## 3. Ollama

Install Ollama and make sure the Ollama service is running.

Check:

```bash
ollama --version
```

Pull the required model:

```bash
ollama pull llama3.2:latest
```

You can also test the model:

```bash
ollama run llama3.2:latest
```

---

# Installation

## 1. Clone the repository

After the project is pushed to GitHub:

```bash
git clone <YOUR_REPOSITORY_URL>
```

Enter the project:

```bash
cd shopping-agent
```

---

## 2. Create a Python virtual environment

Windows:

```bash
python -m venv .venv
```

Activate it:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv .venv
```

Activate:

```bash
source .venv/bin/activate
```

---

## 3. Install Python dependencies

Install the required packages:

```bash
pip install ollama pydantic psycopg[binary] python-dotenv
```

The main dependencies are:

```text
ollama
pydantic
psycopg
python-dotenv
```

---

# Database Setup

## 1. Create the database

Open PostgreSQL:

```bash
psql -U postgres
```

Create the database:

```sql
CREATE DATABASE shopping_agent;
```

Exit:

```sql
\q
```

---

## 2. Initialize the database

From the project directory:

```bash
psql -U postgres -d shopping_agent -f schema.sql
```

This creates:

```text
products
inventory
purchases
```

and inserts the initial sample products.

The sample inventory includes:

| Product             | Stock |
| ------------------- | ----: |
| Gaming Laptop       |     5 |
| Wireless Mouse      |    10 |
| Mechanical Keyboard |     0 |
| USB-C Hub           |     7 |

---

## 3. Configure `.env`

Create a `.env` file in the project root:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=shopping_agent
DB_USER=postgres
DB_PASSWORD=your_password
```

Replace:

```text
your_password
```

with your PostgreSQL password.

Do not commit `.env` to Git.

The `.gitignore` file should contain:

```gitignore
.venv/
__pycache__/
.env
```

---

# Run the Agent

Make sure:

1. PostgreSQL is running.
2. Ollama is running.
3. `llama3.2:latest` is available.
4. The Python virtual environment is activated.

Then run:

```bash
python main.py
```

Choose a role:

```text
customer
```

or:

```text
admin
```

Then enter your request.

Example:

```text
Find me a laptop
```

or:

```text
Find me a laptop and buy one if it is in stock.
```

---

# Testing Permission Control

## Customer

Run:

```bash
python main.py
```

Choose:

```text
customer
```

Then:

```text
Buy one laptop.
```

The agent may identify the laptop and check its stock, but the application harness will reject the purchase:

```text
PERMISSION_DENIED
```

because:

```text
customer → buy_product ✗
```

---

## Admin

Run:

```bash
python main.py
```

Choose:

```text
admin
```

Then:

```text
Find me a laptop and buy one if it is in stock.
```

The admin is allowed to use:

```text
search_product ✓
check_stock ✓
buy_product ✓
```

---

# Summary

This project demonstrates a minimal autonomous agent architecture:

```text
                 USER
                   │
                   ▼
             ┌───────────┐
             │   Ollama  │
             │ LLM Agent │
             └─────┬─────┘
                   │
                   ▼
             Tool Request
                   │
                   ▼
             ┌───────────┐
             │  Harness  │
             │           │
             │ Permission│
             │ Validation│
             │ Call Limit│
             └─────┬─────┘
                   │
                Allowed
                   │
                   ▼
             ┌───────────┐
             │   Tools   │
             └─────┬─────┘
                   │
                   ▼
             ┌───────────┐
             │ PostgreSQL│
             └─────┬─────┘
                   │
                   ▼
               Tool Result
                   │
                   ▼
             ┌───────────┐
             │   Ollama  │
             │ Next Step │
             └─────┬─────┘
                   │
             ┌─────┴─────┐
             │           │
          More Tools   Complete
             │           │
             ▼           ▼
          Tool Call   Final Answer
```

The core principle is:

> **The LLM decides what tool it wants to use, but the application decides whether that tool is allowed to execute.**

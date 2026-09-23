import json
import ollama

from tools import (
    search_product,
    check_stock,
    buy_product,
)

from harness import authorize_tool_call


MODEL = "llama3.2:latest"


MAX_TOOL_CALLS = 5


# Tool schemas exposed to the LLM

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_product",
            "description": (
                "Search for products by name or category. "
                "Use this when the user wants to find a product."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Product name or category to search for"
                        ),
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_stock",
            "description": (
                "Check the current stock of a specific product. "
                "Use the product ID returned by search_product."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "integer",
                        "description": "ID of the product",
                    }
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buy_product",
            "description": (
                "Purchase a product. "
                "Only use this when the user explicitly wants to buy "
                "a product and the product is confirmed to be in stock."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "integer",
                        "description": "ID of the product to purchase",
                    },
                    "quantity": {
                        "type": "integer",
                        "description": (
                            "Number of products to purchase. "
                            "Must be between 1 and 2."
                        ),
                    },
                },
                "required": [
                    "product_id",
                    "quantity",
                ],
            },
        },
    },
]


# Actual tool dispatcher

def execute_tool(
    role: str,
    tool_name: str,
    arguments: dict,
    tool_call_count: int,
) -> dict:

    # Application-level permission + validation

    authorization = authorize_tool_call(
        role=role,
        tool_name=tool_name,
        arguments=arguments,
        tool_call_count=tool_call_count,
    )

    if not authorization["allowed"]:
        return {
            "status": "error",
            "error_code": authorization["error"],
            "message": authorization["message"],
        }

    validated_input = authorization["input"]

    # Execute the actual tool

    if tool_name == "search_product":
        return search_product(validated_input)

    if tool_name == "check_stock":
        return check_stock(validated_input)

    if tool_name == "buy_product":
        return buy_product(validated_input)

    # This should never happen because the harness
    # validates the tool name.
    return {
        "status": "error",
        "error_code": "UNKNOWN_TOOL",
        "message": f"Unknown tool: {tool_name}",
    }


# Agent loop

def run_agent(
    user_request: str,
    role: str = "customer",
) -> str:

    messages = [
        {
            "role": "system",
            "content": """
You are a small shopping assistant.

Your available tools are:
- search_product
- check_stock
- buy_product

Follow these rules:

1. Understand the user's request.
2. Use tools when necessary.
3. Use the result of one tool to decide what to do next.
4. If the user asks to buy a product, first identify the product
   and check its stock before attempting to buy it.
5. Do not invent product IDs, prices, stock, or purchase results.
6. Only report information returned by the tools.
7. If a tool returns an error, explain the error to the user.
8. Stop when the user's request has been satisfied.
""",
        },
        {
            "role": "user",
            "content": user_request,
        },
    ]

    tool_call_count = 0

    # Main agent loop

    while tool_call_count < MAX_TOOL_CALLS:

        print("\n" + "=" * 60)
        print("AGENT THINKING / DECISION")
        print("=" * 60)

        response = ollama.chat(
            model=MODEL,
            messages=messages,
            tools=TOOL_DEFINITIONS,
        )

        assistant_message = response["message"]

        # Add assistant response to conversation
        messages.append(assistant_message)

        # Check whether the LLM requested a tool
        tool_calls = assistant_message.get("tool_calls", [])

        # No tool call = final answer
        if not tool_calls:

            print("\nAGENT FINAL ANSWER")
            print("-" * 60)

            return assistant_message.get(
                "content",
                "The agent did not provide a final answer.",
            )

        # Execute requested tools
        for tool_call in tool_calls:

            tool_name = tool_call["function"]["name"]

            arguments = tool_call["function"].get(
                "arguments",
                {},
            )

            # Some Ollama responses may return arguments
            # as a JSON string.
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {}

            tool_call_count += 1

            print("\nTOOL REQUEST")
            print("-" * 60)
            print(f"Tool: {tool_name}")
            print(f"Arguments: {arguments}")
            print(f"Tool call: {tool_call_count}/{MAX_TOOL_CALLS}")

            # Application executes / rejects the request
            result = execute_tool(
                role=role,
                tool_name=tool_name,
                arguments=arguments,
                tool_call_count=tool_call_count,
            )

            print("\nTOOL RESULT")
            print("-" * 60)
            print(json.dumps(result, indent=2))

            # Return tool result to the LLM
            messages.append(
                {
                    "role": "tool",
                    "content": json.dumps(result),
                }
            )

            # Stop if maximum tool calls reached
            if tool_call_count >= MAX_TOOL_CALLS:

                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "The maximum number of tool calls has "
                            "been reached. Provide the best final "
                            "answer using the information already "
                            "available."
                        ),
                    }
                )

                break

    return (
        "The agent stopped because the maximum tool-call "
        "limit was reached."
    )
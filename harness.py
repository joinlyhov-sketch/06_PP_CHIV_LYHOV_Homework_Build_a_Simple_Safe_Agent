from schemas import (
    SearchProductInput,
    CheckStockInput,
    BuyProductInput,
)


# --------------------------------------------------
# Permissions
# --------------------------------------------------

ROLE_PERMISSIONS = {
    "customer": {
        "search_product",
        "check_stock",
    },
    "admin": {
        "search_product",
        "check_stock",
        "buy_product",
    },
}


# --------------------------------------------------
# Tool permissions
# --------------------------------------------------

def check_permission(role: str, tool_name: str) -> bool:
    """
    Check whether a role is allowed to execute a tool.
    """

    allowed_tools = ROLE_PERMISSIONS.get(role)

    if allowed_tools is None:
        return False

    return tool_name in allowed_tools


# --------------------------------------------------
# Maximum tool calls
# --------------------------------------------------

MAX_TOOL_CALLS = 8


def check_tool_call_limit(tool_call_count: int) -> bool:
    """
    Prevent the agent from running forever.
    """

    return tool_call_count < MAX_TOOL_CALLS


# --------------------------------------------------
# Tool input validation
# --------------------------------------------------

def validate_tool_input(tool_name: str, arguments: dict):
    """
    Validate tool arguments using Pydantic schemas.
    """

    if tool_name == "search_product":
        return SearchProductInput(**arguments)

    if tool_name == "check_stock":
        return CheckStockInput(**arguments)

    if tool_name == "buy_product":
        return BuyProductInput(**arguments)

    raise ValueError(f"Unknown tool: {tool_name}")


# --------------------------------------------------
# Central safety check
# --------------------------------------------------

def authorize_tool_call(
    role: str,
    tool_name: str,
    arguments: dict,
    tool_call_count: int,
):
    """
    Check permission, tool-call limit,
    and input validation.
    """

    # 1. Check tool-call limit
    if not check_tool_call_limit(tool_call_count):
        return {
            "allowed": False,
            "error": "TOOL_CALL_LIMIT",
            "message": "Maximum tool-call limit reached.",
        }

    # 2. Check permission
    if not check_permission(role, tool_name):
        return {
            "allowed": False,
            "error": "PERMISSION_DENIED",
            "message": (
                f"Role '{role}' is not allowed "
                f"to execute '{tool_name}'."
            ),
        }

    # 3. Validate arguments
    try:
        validated_input = validate_tool_input(
            tool_name,
            arguments,
        )

    except Exception as exc:
        return {
            "allowed": False,
            "error": "INVALID_INPUT",
            "message": str(exc),
        }

    return {
        "allowed": True,
        "input": validated_input,
    }
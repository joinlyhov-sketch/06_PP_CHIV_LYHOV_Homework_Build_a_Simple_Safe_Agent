# from agent import run_agent


# def main():
#     print("=" * 60)
#     print("SHOPPING AGENT")
#     print("=" * 60)

#     print("\nAvailable roles:")
#     print("1. customer")
#     print("2. admin")

#     role = input("\nEnter role [customer/admin]: ").strip().lower()

#     if role not in {"customer", "admin"}:
#         print("Invalid role.")
#         return

#     user_request = input(
#         "\nWhat would you like to do?\n> "
#     ).strip()

#     if not user_request:
#         print("Request cannot be empty.")
#         return

#     print("\nStarting agent...")

#     final_answer = run_agent(
#         user_request=user_request,
#         role=role,
#     )

#     print("\n" + "=" * 60)
#     print("FINAL ANSWER")
#     print("=" * 60)
#     print(final_answer)


# if __name__ == "__main__":
#     main()

from agent import run_agent


def main():

    print("=" * 60)
    print("SHOPPING AGENT")
    print("=" * 60)

    print("\nAvailable roles:")
    print("1. customer")
    print("2. admin")

    role = input(
        "\nEnter role [customer/admin]: "
    ).strip().lower()

    if role not in {"customer", "admin"}:
        print("Invalid role.")
        return

    print("\nExample questions you can ask:")
    print("  1. Find me a laptop.")
    print("  2. Find a wireless mouse.")
    print("  3. Check stock for product 1.")
    print("  4. Buy 1 unit of product 1.")
    print("  5. Find a laptop and buy one if it is in stock.")
    print("\nType 'exit' to quit.")

    while True:

        print("\n" + "=" * 60)

        user_request = input(
            "What would you like to do?\n> "
        ).strip()

        # Exit the agent session
        if user_request.lower() in {"exit", "quit"}:
            print("\nGoodbye!")
            break

        # Ignore empty input
        if not user_request:
            print("Request cannot be empty.")
            continue

        print("\nStarting agent...")

        final_answer = run_agent(
            user_request=user_request,
            role=role,
        )

        print("\n" + "=" * 60)
        print("FINAL ANSWER")
        print("=" * 60)
        print(final_answer)


if __name__ == "__main__":
    main()
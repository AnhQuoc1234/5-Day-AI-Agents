def add(a: float, b: float) -> float:
    """Return the sum of a and b."""
    return a + b

def subtract(a: float, b: float) -> float:
    """Return the difference of a and b."""
    return a - b

def multiply(a: float, b: float) -> float:
    """Return the product of a and b."""
    return a * b

def divide(a: float, b: float) -> float:
    """Return the quotient of a divided by b. Raise ValueError on division by zero."""
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return a / b

def main():
    print("Welcome to Simple Calculator")
    print("Operations: +, -, *, /, or 'exit' to quit")
    while True:
        try:
            op = input("Enter operation: ").strip()
            if op.lower() == 'exit':
                print("Goodbye!")
                break
            if op not in ('+', '-', '*', '/'):
                print("Invalid operation. Please use +, -, *, or /.")
                continue
            
            num1 = float(input("Enter first number: "))
            num2 = float(input("Enter second number: "))
            
            if op == '+':
                print(f"Result: {add(num1, num2)}")
            elif op == '-':
                print(f"Result: {subtract(num1, num2)}")
            elif op == '*':
                print(f"Result: {multiply(num1, num2)}")
            elif op == '/':
                try:
                    print(f"Result: {divide(num1, num2)}")
                except ValueError as e:
                    print(e)
        except ValueError:
            print("Invalid input. Please enter valid numbers.")
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    main()

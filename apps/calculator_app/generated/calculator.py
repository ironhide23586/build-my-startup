import sys

def add_numbers(num1, num2):
    return num1 + num2

def subtract_numbers(num1, num2):
    return num1 - num2

def validate_input(user_input):
    try:
        return float(user_input)
    except ValueError:
        return None

def write_result_to_file(result):
    with open('results.txt', 'a') as file:
        file.write(f'{result}\n')

def main():
    print("Welcome to the CLI Calculator!")
    while True:
        operation = input("Enter operation (+ or -) or 'exit' to quit: ").strip()
        if operation.lower() == 'exit':
            print("Exiting the calculator. Goodbye!")
            break
        if operation not in ('+', '-'):
            print("Invalid operation. Please enter + or -.")
            continue
        
        num1_input = input("Enter the first number: ")
        num2_input = input("Enter the second number: ")
        
        num1 = validate_input(num1_input)
        num2 = validate_input(num2_input)
        
        if num1 is None or num2 is None:
            print("Invalid input. Please enter numeric values.")
            continue
        
        if operation == '+':
            result = add_numbers(num1, num2)
        else:
            result = subtract_numbers(num1, num2)
        
        print(f"The result is: {result}")
        write_result_to_file(result)

if __name__ == "__main__":
    main()
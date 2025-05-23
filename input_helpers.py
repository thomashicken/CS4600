def get_valid_input(prompt, valid_fn, error_msg):
    while True:
        val = input(prompt).strip()
        if valid_fn(val):
            return val
        print(error_msg)

def get_valid_float(prompt):
    while True:
        try:
            return float(input(prompt).strip())
        except ValueError:
            print("Invalid number. Please enter a valid float.")

def get_valid_int(prompt):
    while True:
        try:
            return int(input(prompt).strip())
        except ValueError:
            print("Invalid number. Please enter a valid integer.")

def get_optional_float(prompt, default):
    while True:
        val = input(prompt).strip()
        if not val:
            return default  # User pressed Enter, use default
        try:
            return float(val)
        except ValueError:
            print("Invalid input. Please enter a valid number.")

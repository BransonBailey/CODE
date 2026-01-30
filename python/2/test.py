def greet(name):
    print("Hello, " + name)

def add_numbers(a, b):
    return a+b  # Missing space around the operator

def main():
    greet("Alice")
    print(add_numbers(5, 10))
    
    # This will throw a NameError since 'x' is not defined
    print(x)

if __name__ == "__main__":
    main()


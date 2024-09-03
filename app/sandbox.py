def add (a,b):
    return a+b

def main():
    return add(1, 2)  # Updated to return the result of add

if __name__ == "__main__":
    result = main()
    if result > 2:
        print("Result is greater than 2")
    else:
        print("Result is less than 2")


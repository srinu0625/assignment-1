print("Think of a number between 1 and 100.")
input("Press Enter when you are ready...")

low = 1
high = 100

while True:
    guess = (low + high) // 2
    print(f"\nIs your number {guess}?")

    response = input("Type 'h' if my guess is too high, 'l' if too low, 'c' if correct: ").lower()

    if response == "c":
        print(f"\n😎 I read your mind! Your number is {guess}.")
        break
    elif response == "h":
        high = guess - 1
    elif response == "l":
        low = guess + 1
    else:
        print("Please type only h, l, or c.")
        
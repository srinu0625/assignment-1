import random

user_choice = int(input("Choose a number:\nType 0 for rock\nType 1 for paper\nType 2 for scissors\n"))

computer_choice = random.randint(0, 2)
print("Computer's choice =", computer_choice)

if computer_choice == user_choice:
    print("\033[32m------------DRAW--------------\033")
elif (computer_choice == 0 and user_choice == 2) or \
        (computer_choice == 1 and user_choice == 0) or \
        (computer_choice == 2 and user_choice == 1):
    print("\033[31m---------You lose------------\033")
else:
    print("\033[32m---------You win--------------\033")

nani=4
while nani<=4:
    print(nani)
    nani+=1

import random

letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k',
           'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
symbols = ['!', '@', '#', '$', '%', '^', "&", '*', ".."]

n_letters = int(input("how many letters do you want?\n"))
n_numbers = int(input("how many numbers do you want?\n"))
n_symbols = int(input("how many symbols do you want?\n"))

password_list = []

# Generate letters
for i in range(n_letters):
    char = random.choice(letters)
    password_list.append(char)

# Generate symbols
for i in range(n_symbols):
    char = random.choice(symbols)
    password_list.append(char)

# Generate numbers
for i in range(n_numbers):
    char = random.choice(numbers)
    password_list.append(char)

# Shuffle the password components
random.shuffle(password_list)

# Join the shuffled components to form the password
password = ''.join(password_list)

print(password)

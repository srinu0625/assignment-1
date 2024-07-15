import random
import hangman_stages

# Assuming you have a module named hangman_stages with the stages defined
# If not, define the stages list in this file

word_list = ['apple', 'ball', 'carrot', 'banana', 'bike', 'bus']
lifes = 6
chosen_word = random.choice(word_list)
print(chosen_word)
display = ['_' for _ in chosen_word]

game_over = False
while not game_over:
    guess_letter = input("Guess a letter: ").lower()
    found = False
    for position in range(len(chosen_word)):
        letter = chosen_word[position]
        if letter == guess_letter:
            display[position] = guess_letter
            found = True
    print(display)

    if not found:
        lifes -= 1
        if lifes == 0:
            game_over = True
            print('You Lose')

    if '_' not in display:
        game_over = True
        print('You WIN')

    print(hangman_stages.stages[lifes])

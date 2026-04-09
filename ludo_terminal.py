import random

# CONFIG
TARGET = 30
TOKENS = 4

# Player state
players = {
    "A": {"tokens": [0]*TOKENS},
    "B": {"tokens": [0]*TOKENS}
}

current = "A"

def roll():
    return random.randint(1, 6)

def all_home(player):
    return all(t >= TARGET for t in players[player]["tokens"])

def print_state():
    print("\n--- GAME STATE ---")
    for p in players:
        print(f"{p}: {players[p]['tokens']}")
    print("------------------\n")

while True:
    print_state()
    print(f"Player {current} turn (Press Enter to roll)")
    input()

    dice = roll()
    print(f"{current} rolled: {dice}")

    tokens = players[current]["tokens"]

    # Show movable tokens
    movable = []
    for i, pos in enumerate(tokens):
        if pos == 0 and dice == 6:
            movable.append(i)
        elif pos > 0 and pos < TARGET:
            movable.append(i)

    if not movable:
        print("No moves possible.")
    else:
        print(f"Choose token {movable}: ", end="")
        choice = int(input())

        # ENTER BOARD
        if tokens[choice] == 0 and dice == 6:
            tokens[choice] = 1
        else:
            tokens[choice] += dice

        # KILL LOGIC
        opponent = "B" if current == "A" else "A"
        for i, pos in enumerate(players[opponent]["tokens"]):
            if pos == tokens[choice] and pos != 0 and pos < TARGET:
                print(f"🔥 {current} killed {opponent}'s token!")
                players[opponent]["tokens"][i] = 0

    # CHECK WIN
    if all_home(current):
        print(f"\n🎉 Player {current} WINS!")
        break

    # EXTRA TURN IF 6
    if dice != 6:
        current = "B" if current == "A" else "A"
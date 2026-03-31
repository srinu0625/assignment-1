def flames_game():
    while True:
        print("\n FLAMES GAME ")

        name1 = input("Enter first name: ").lower().replace(" ", "")
        name2 = input("Enter second name: ").lower().replace(" ", "")

        # Convert to list
        list1 = list(name1)
        list2 = list(name2)

        # Remove common letters
        for ch in name1:
            if ch in list2:
                list1.remove(ch)
                list2.remove(ch)

        # Count remaining letters
        count = len(list1) + len(list2)

        flames = ["F", "L", "A", "M", "E", "S"]

        # Game logic
        while len(flames) > 1:
            index = (count % len(flames)) - 1

            if index >= 0:
                flames = flames[index+1:] + flames[:index]
            else:
                flames = flames[:-1]

        result_dict = {
            "F": "Friends ",
            "L": "Love ",
            "A": "Affection ",
            "M": "Marriage ",
            "E": "Enemy ",
            "S": "Siblings "
        }

        print("\nResult:", result_dict[flames[0]])

        # Play again option
        again = input("\nDo you want to play again? (yes/no): ").lower()
        if again != "yes":
            print("Thanks for playing! 👋")
            break


# Run the game
flames_game()
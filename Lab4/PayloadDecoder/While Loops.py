guess = 0
guessed = False

for i in range(0, 5):
    print("Guess A Number: ")
    guess = int(input("\n"))

    if guess == 20:
        guessed = True
        break
    elif guess != 20 and i != 0:
        print("Try Again!: " + str(5 - (i + 1)) + " More Guesses!")

if guessed:
    print("Good Job!")
else:
    print("Trash!")


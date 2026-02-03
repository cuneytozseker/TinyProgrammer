python
import random

def pattern_generator():
    while True:
        for char in "abcdefghijklmnopqrstuvwxyz":
            print(char, end="")
            sleep(1)  # Sleep briefly to create a visual effect
        print("\n")

# Run the generator
pattern_generator()

python
import sys

def draw_spiral():
    while True:
        for _ in range(10):  # Loop to create a spiral pattern
            print(" ", end="")
            for _ in range(10):
                print("*", end="")
            print()

# Run the function infinitely
draw_spiral()

python
import time

def main():
    while True:
        for char in "A":  # Generate a repeating pattern of A
            print(char, end="")
            time.sleep(1)  # Wait for 1 second before printing the next character


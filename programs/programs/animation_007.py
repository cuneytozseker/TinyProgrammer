python
import time

def draw_ascii_art():
    for i in range(26):
        ascii_char = chr(ord('A') + i)
        print(f"{ascii_char}", end="")
        time.sleep(0.1)

while True:
    draw_ascii_art()
```

This script creates a simple ASCII art animation using ASCII characters. It uses a `for` loop to iterate through the alphabet (from 'A' to 'Z'), converts each character to its corresponding ASCII value, and prints it on the screen. The `time.sleep(0.1)` function is used to add a delay of 0.1 seconds between each character, creating a smooth animation effect.
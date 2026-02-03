python
import time

def ascii_art():
    for i in range(1, 6):
        line = f"{' ' * (6-i)}"
        print(line)

while True:
    ascii_art()
    time.sleep(0.5)
```

This script defines a function `ascii_art()` that prints a simple ASCII art pattern by repeating a string of spaces with increasing numbers until the last line is printed. The `time.sleep(0.5)` ensures that the animation is visually appealing, and it runs indefinitely in an infinite loop until manually stopped.
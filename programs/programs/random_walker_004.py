python
import time
import random

def draw_dot(x, y):
    print(chr(27) + f'\x1b[38;48m({x}, {y})\x1b[0m', end='')

while True:
    x = random.randint(0, 69)
    y = random.randint(0, 39)
    draw_dot(x, y)
    time.sleep(0.2)  # Simulate walking
```

This script creates a screen with dots randomly moving around within the boundaries of the screen. It uses ASCII characters to visually represent each dot and pauses for a short interval to simulate movement.
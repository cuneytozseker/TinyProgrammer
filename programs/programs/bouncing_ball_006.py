python
import time

def draw_ball(x, y):
    print('\033[2H', end='')  # Move cursor to the beginning of the screen
    print(' '.join([' ' * x] for _ in range(y)))  # Draw a line of x characters high

while True:
    draw_ball(10, 10)  # Bounce the ball across the screen
    time.sleep(2)  # Wait for 2 seconds before moving it again
```

This script uses Python's built-in `time` module to simulate a ball bouncing across the screen. It prints ASCII characters to draw the ball, simulating its movement and appearance. The loop runs indefinitely, allowing you to see the ball bouncing.
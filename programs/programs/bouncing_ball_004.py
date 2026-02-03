```
import time

def draw_bouncing_ball(x, y):
    while True:
        print(" ", end="")
        for _ in range(10):  # Draw a circle
            print("*", end=" ")
            time.sleep(0.05)
        print("\n")
        x += 1
        if x > 100:  # Wrap around the screen if it goes beyond the left edge
            x = 1

while True:
    draw_bouncing_ball(10, 10)  # Initial position and color of the ball
    time.sleep(5)

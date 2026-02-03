python
import time

def draw_ball(x, y):
    print(chr(27), end='')  # Reset colors to default
    print(chr(65 + x), end='')  # Move left on screen
    print(chr(90 + y), end='')  # Move up on screen
    print(chr(122 + y), end='')  # Move right on screen
    print(' ', end='')  # Print a space for readability

def bounce_ball(x, y):
    ball_radius = 50
    while True:
        x += 1  # Move left
        if (x - ball_radius) < 0:  # Out of bounds
            x -= ball_radius
            break
        draw_ball(x, y)
        time.sleep(0.1)

draw_ball(200, 300)
while True:
    bounce_ball(200, 300)

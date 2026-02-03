python
import random

def draw_dot():
    x = random.randint(0, screen_width)
    y = random.randint(0, screen_height)
    pygame.draw.circle(screen, (255, 0, 0), (x, y), radius=10)

def animate_dots():
    while True:
        screen.fill((0, 0, 0))  # Clear the screen
        draw_dot()
        time.sleep(0.05)   # Update the display every 0.05 seconds


python
import time
import random
import math

def draw_dot(x, y):
    # Simulate a dot moving randomly
    radius = 5 + (math.sqrt(2) * random.random())
    return pygame.draw.circle(screen, (0, 255, 0), (x, y), radius)

running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((0, 0, 0))  # Clear the screen
    draw_dot(random.randint(100, 500), random.randint(100, 500))  # Move a dot
    pygame.display.flip()  # Update the display

    clock.tick(60)  # Maintain an average frame rate of 60 FPS

pygame.quit()

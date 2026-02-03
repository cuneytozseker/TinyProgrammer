python
import time

# Initialize screen dimensions
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Bouncing Ball")

while True:
    # Clear the screen
    screen.fill((0, 0, 0))
    
    # Draw a small ball at the center of the screen
    pygame.draw.circle(screen, (255, 255, 255), (width // 2, height // 2), 30)
    
    # Update the display
    pygame.display.flip()
    
    # Wait for a short period to simulate animation
    time.sleep(1 / 60)

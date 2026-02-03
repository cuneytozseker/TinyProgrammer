python
import random

# Define the screen dimensions
width, height = 800, 600

# Function to draw a circle on the screen
def draw_circle(x, y):
    # Draw a black circle at (x, y)
    pygame.draw.circle(screen, (0, 0, 0), (x, y), 25)

# Main loop to continuously animate the dot
while True:
    for _ in range(100):  # Simulate an animation loop with a delay of 100ms
        x = random.randint(0, width - 25)
        y = random.randint(0, height - 25)
        
        draw_circle(x, y)
```

This script uses the `pygame` library to create a window and animate a dot moving around the screen. The dot is drawn at a random position within the specified dimensions. The loop runs for 100 milliseconds (1 second), simulating an animation effect.
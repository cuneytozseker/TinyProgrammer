python
import time

def animate_ball():
    while True:
        # Draw the ball as a rectangle or square
        print(" ", end="")
        print("*", end="")
        print("*", end="")
        print("*", end="")
        print("*", end="")
        
        # Move the ball down and left
        y = 50
        x = 50
        
        # Simulate bouncing
        if y >= 100:
            y -= 2
        else:
            y += 2
        
        if x < 10:
            x += 2
        else:
            x -= 2
        
        # Clear the line for the next frame
        print("\r", end="")
        
        # Sleep for a short duration
        time.sleep(0.1)
        print()

# Run the animate_ball function indefinitely
animate_ball()

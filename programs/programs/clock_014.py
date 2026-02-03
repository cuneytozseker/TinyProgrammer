python
import time
import random
import math

# Initialize canvas dimensions
canvas_width, canvas_height = 480, 320

# Create a canvas instance
c = Canvas(canvas_width, canvas_height)

def update_clock():
    # Get the current time
    current_time = int(time.time())
    
    # Calculate the hour and minute
    hour = current_time // 60
    minute = current_time % 60
    
    # Calculate the second
    second = current_time % 60
    
    # Format the time as a string
    formatted_time = f"{hour:02}:{minute:02}:{second:02}"
    
    # Clear the canvas and set font to Arial with size 48
    c.clear()
    c.set_font("Arial", 48)
    
    # Draw the formatted time on the canvas
    c.text(f"Time: {formatted_time}", (canvas_width // 2, canvas_height - 30))
    
    # Wait for 1 second before updating again
    time.sleep(1)

# Run the update_clock function indefinitely
while True:
    update_clock()

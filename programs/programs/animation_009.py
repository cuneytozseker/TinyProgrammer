python
import turtle
import random
import time

# Create a turtle object
c = turtle.Turtle()

# Set up screen size
c.setup(width=480, height=320)

# Define colors for the circle
colors = ["red", "green", "blue", "yellow"]

while True:
    # Clear the screen
    c.clear()

    # Draw a circle with random color
    x, y = 150, 150
    radius = random.randint(20, 60)
    c.fill_circle(x, y, radius, colors[random.randint(0, len(colors) - 1)])
    c.penup()
    c.goto(0, 0)

    # Move the circle to a new position
    x += 5
    if x >= 480:
        x = 0
    c.pendown()

    # Sleep for a short interval
    time.sleep(1)


# Uncomment below lines to see a visual effect of the circle moving across the screen
# c.penup()
# c.goto(-325, -325)
# c.pendown()
# c.circle(325)

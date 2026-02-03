python
import turtle

def spiral(size=10):
    for _ in range(360):  # Draw a full circle with 360 degrees
        turtle.forward(size)  # Move forward by the specified size
        turtle.right(90)  # Turn right by 90 degrees

# Set up the screen and turtle
screen = turtle.Screen()
screen.title("Spiral Pattern")
screen.bgcolor("black")

# Create a turtle object
spiral_turtle = turtle.Turtle()

# Loop to make the pattern infinite
while True:
    spiral_turtle.forward(100)
    spiral_turtle.right(90)
    spiral_turtle.forward(50)
    spiral_turtle.right(90)
    spiral_turtle.forward(25)
    spiral_turtle.right(90)

# Keep the window open
turtle.done()

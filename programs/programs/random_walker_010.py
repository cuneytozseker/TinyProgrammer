python
import turtle

def draw_dot(x, y):
    """Draws a single dot at the specified (x, y) position."""
    r = 50
    g = 50
    b = 50
    c.fill_rect(x, y, r, r, r, g, b)
    # Infinite loop using only standard libraries
    while True:
        turtle.forward(10)  # Move forward by 10 units

# Example usage
draw_dot(0, 0)

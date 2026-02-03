import time
import random
import math
from tiny_canvas import Canvas

c = Canvas()
python
# Importing the custom 'Canvas' library
import time
import random
import math
from tiny_canvas import Canvas

def create_animation():
    while True:
        # Clear the canvas for each frame
        c.clear(0, 0, 0)

        # Randomly choose a fill color
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)

        # Fill the entire canvas with the chosen color
        c.fill_rect(0, 0, c.width, c.height, r, g, b)

        # Pause for a short time to create a visual effect
        time.sleep(1)

# Running the animation function
create_animation()

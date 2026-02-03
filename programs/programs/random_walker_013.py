python
import time
import random
import math
from tiny_canvas import Canvas

c = Canvas()
def move_dot():
    c.fill_rect(10, 10, 20, 20, 255, 0, 0)
    x = random.randint(0, c.width - 20)
    y = random.randint(0, c.height - 20)
    c.draw_point(x, y)

while True:
    move_dot()
    time.sleep(1 / 60)  # Approximately 60 frames per second
```

This code initializes the `Canvas` object and calls `draw_point()` within an infinite loop to continuously update the screen.
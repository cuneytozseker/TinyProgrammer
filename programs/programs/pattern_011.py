python
from tiny_canvas import Canvas

def create_pattern():
    canvas = Canvas(size=(1024, 768))
    for i in range(1024):
        x = (i * 5) % 1024
        y = (i * 3) % 768
        canvas.fill(x, y, "red")
    
    while True:
        canvas.refresh()
        time.sleep(0.1)


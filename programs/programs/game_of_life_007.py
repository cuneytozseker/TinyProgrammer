import time
import random
import math
from tiny_canvas import Canvas

c = Canvas()
python
def draw_cell(x, y):
    c.fill_circle(x, y, 1, 255, 0, 0)

def update_cells():
    for row in range(len(c.grid)):
        for col in range(len(c.grid[row])):
            if c.grid[row][col] == 1:
                neighbors = sum([c.grid[r + dx][c.grid[cy + dy]] for dx in [-1, 0, 1] for dy in [-1, 0, 1]])
                if neighbors < 2 or neighbors > 3:
                    c.clear(row, col)
    # Clear the remaining cells
    for row in range(len(c.grid)):
        for col in range(len(c.grid[row])):
            if not (c.grid[row][col] == 1 and neighbors == 3):
                c.fill_cell(row, col)

def draw_grid():
    for i in range(50):
        for j in range(50):
            draw_cell(i, j)


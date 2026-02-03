python
import time
import random
import math

# Define the size of the grid
GRID_SIZE = 20

# Create a 2D list to represent the grid
grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

def update_grid(grid):
    # Iterate over each cell in the grid
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            # Count the number of live neighbors
            live_neighbors = sum(1 for x, y in [(i-1, j), (i+1, j), (i, j-1), (i, j+1)] if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE and grid[x][y] == 1)
            
            # Apply the rules of Conway's Game of Life
            if grid[i][j]:
                if live_neighbors < 2 or live_neighbors > 3:
                    # Cell is dead
                    grid[i][j] = 0
                else:
                    # Cell is alive
                    grid[i][j] = 1

def main():
    while True:
        update_grid(grid)
        print("Current grid:")
        for row in grid:
            print(row)
        time.sleep(1)  # Sleep for 1 second before updating the grid again


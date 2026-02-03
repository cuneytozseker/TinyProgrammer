python
def main():
    grid = [
        [0, 0, 1, 0],
        [0, 1, 1, 0],
        [1, 0, 0, 1],
        [0, 0, 0, 1]
    ]

    while True:
        for row in range(len(grid)):
            for col in range(len(grid[row])):
                # Check if the cell is alive or dead
                if grid[row][col] == 1:
                    # Count adjacent cells to determine cell's state
                    live_neighbors = sum(1 for r, c in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))
                    if live_neighbors < 2 or live_neighbors > 3:
                        grid[row][col] = 0
                else:
                    # Cell is dead
                    if live_neighbors == 3:
                        grid[row][col] = 1

        # Print the updated grid
        for row in range(len(grid)):
            print(' '.join(str(cell) if cell != 0 else ' ') for cell in grid[row])


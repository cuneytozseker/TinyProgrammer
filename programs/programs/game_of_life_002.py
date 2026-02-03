python
def main():
    grid = [
        [0, 1, 0],
        [0, 1, 0],
        [0, 1, 0]
    ]
    while True:
        print('\n'.join([''.join(map(str, row)) for row in grid]))
        
        new_grid = [[0] * len(grid[0]) for _ in range(len(grid))]
        
        for i in range(len(grid)):
            for j in range(len(grid[0])):
                if grid[i][j] == 1:
                    neighbors = 0
                    for x, y in [(i+1, j), (i-1, j), (i, j+1), (i, j-1), (x+1, y+1), (x+1, y-1), (x-1, y+1), (x-1, y-1)]:
                        if 0 <= x < len(grid) and 0 <= y < len(grid[0]):
                            neighbors += grid[x][y]
                    if neighbors == 3:
                        new_grid[i][j] = 1
                    elif neighbors == 2 or neighbors == 0:
                        new_grid[i][j] = 0
                else:
                    new_grid[i][j] = grid[i][j]

        grid = new_grid


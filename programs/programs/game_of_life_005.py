python
def main():
    rows, cols = 10, 10
    grid = [[0] * cols for _ in range(rows)]
    
    while True:
        print("\n".join([" ".join(map(str, row)) for row in grid]))
        
        # Update the grid based on Conway's rules
        new_grid = []
        for i in range(rows):
            for j in range(cols):
                live_neighbors = 0
                
                if i > 0 and grid[i-1][j] == 1:
                    live_neighbors += 1
                if i < rows - 1 and grid[i+1][j] == 1:
                    live_neighbors += 1
                if j > 0 and grid[i][j-1] == 1:
                    live_neighbors += 1
                if j < cols - 1 and grid[i][j+1] == 1:
                    live_neighbors += 1
                
                if grid[i][j] == 0 and live_neighbors == 3:
                    new_grid.append(1)
                elif grid[i][j] == 1 and (live_neighbors == 2 or live_neighbors == 3):
                    new_grid.append(1)
                else:
                    new_grid.append(0)
        
        # Update the grid with the new values
        grid = new_grid
    
    return


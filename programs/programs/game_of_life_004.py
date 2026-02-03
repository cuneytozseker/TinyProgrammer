python
def main():
    grid = [
        [0, 1, 0],
        [0, 0, 1],
        [1, 1, 1]
    ]
    
    while True:
        for row in grid:
            print(' '.join(map(str, row)))
        
        new_grid = []
        for row in grid:
            new_row = []
            for cell in row:
                if cell == 0:
                    new_row.append(0)
                else:
                    new_row.append(1)
            new_grid.append(new_row)
        
        grid = new_grid
    

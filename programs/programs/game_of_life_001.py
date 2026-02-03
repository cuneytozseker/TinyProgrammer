To implement Conway's Game of Life in a simple grid, we need to create a function that takes a 2D list representing the game board and updates it based on the rules of the game. Here's a Python script that implements this:

python
import time
import random

def is_alive(x, y, board):
    return (board[x][y] == 1) or ((x > 0) and (y > 0)) and (x < len(board) - 1) and (y < len(board[0]) - 1)

def update_board(board):
    new_board = [[0] * len(board[0]) for _ in range(len(board))]
    for i in range(len(board)):
        for j in range(len(board[i])):
            if is_alive(i, j, board):
                neighbors = 0
                for dx, dy in [(-1, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (1, 1)]:
                    nx, ny = i + dx, j + dy
                    if is_alive(nx, ny, board):
                        neighbors += 1
                if board[i][j] == 1 and neighbors < 2 or board[i][j] == 0 and neighbors > 3:
                    new_board[i][j] = 0
                else:
                    new_board[i][j] = 1
    return new_board

def main():
    # Create a small game board with initial random values
    board = [[random.choice([0, 1]) for _ in range(5)] for _ in range(5)]
    
    while True:
        # Update the game board
        updated_board = update_board(board)
        
        # Print the current board
        print("Current Board:")
        for row in board:
            print(row)
        
        # Wait for a short time before updating the next iteration
        time.sleep(1)


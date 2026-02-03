python
# Import necessary libraries
import time

def generate_pattern():
    while True:
        # Print a pattern using ASCII characters
        for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz":
            print(char)
        
        # Wait for 1 second
        time.sleep(1)

generate_pattern()
```

This code snippet defines a function `generate_pattern()` that prints the pattern of uppercase letters and lowercase letters, each on a new line. The loop runs infinitely, continuously printing the same sequence.
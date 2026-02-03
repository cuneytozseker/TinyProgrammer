python
import time

def print_ascii_animation():
    while True:
        # Print the ASCII character 'A' for 1 second, then 'B'
        print('A')
        time.sleep(1)
        print('B')

print_ascii_animation()
```

### Explanation:
- The `while True:` loop runs indefinitely.
- Inside the loop, the `print()` function is used to display the string 'A'.
- After each character 'A' is printed, it waits for 1 second using `time.sleep(1)`.
- This process repeats indefinitely, creating a simple ASCII animation.
python
import time

def create_pattern():
    current_char = 'A'
    while True:
        print(current_char, end='')
        time.sleep(1)  # Simulate a delay
        current_char = chr((ord(current_char) + 1) % 26)

create_pattern()
```

This script prints "A", pauses for a second, and then changes to the next character in the alphabet (A to Z).
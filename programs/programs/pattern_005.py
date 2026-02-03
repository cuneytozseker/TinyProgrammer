python
import time

def repeat_pattern():
    while True:
        # Generate a repeating pattern using ASCII characters
        print("Mesa", end="\r")
        time.sleep(1)  # Wait for a second before printing the next line

# Run the function indefinitely
repeat_pattern()
```

This script will continuously print "Mesa" (ASCII character for "Mesa") to the console, creating a mesmerizing repeating pattern.
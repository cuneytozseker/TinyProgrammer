python
import time

def display_clock():
    while True:
        # Get current time
        now = time.strftime("%H:%M:%S")
        
        # Update the clock on the screen
        print(f"{now}")

# Run the display_clock function indefinitely
display_clock()
```

This Python script defines a function `display_clock` that continuously updates and prints the current time every second. The `time.strftime()` function is used to format the current time as "HH:MM:SS". The `while True:` loop ensures that the clock runs in an infinite loop, allowing it to display real-time information without stopping.
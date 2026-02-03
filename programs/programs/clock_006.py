python
import time

while True:
    print("Time:", time.strftime("%H:%M:%S"))
    time.sleep(1)
```

This script uses the `time` module to display the current time every second. The `print()` function is used to display the time in a human-readable format (e.g., "09:55:30"). The `time.sleep(1)` function pauses the execution for 1 second before displaying the next time.
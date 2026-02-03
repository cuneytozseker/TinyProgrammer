python
import time

while True:
    print("Time: ", end="")
    current_time = time.strftime("%H:%M:%S")
    print(current_time)
    time.sleep(1)  # Wait for one second before updating again
```

This script displays the current time every second, formatted as "HH:MM:SS", in a minimalistic style.
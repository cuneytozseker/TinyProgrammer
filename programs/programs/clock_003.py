python
import time
print("Digital Clock!")

while True:
    current_time = time.strftime("%H:%M:%S")
    print(current_time, end="\r")  # Refreshes every second with a newline character
    time.sleep(1)
```

This code sets up a simple digital clock that updates in real-time. It uses `time.strftime` to get the current time and prints it as a string. The loop runs indefinitely (`while True:`), and it also includes a small delay using `time.sleep(1)`, so the display refreshes every second.
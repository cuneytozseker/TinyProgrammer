python
import time

def display_time():
    current_time = time.strftime("%H:%M:%S")
    print(current_time)

while True:
    display_time()
    time.sleep(1)

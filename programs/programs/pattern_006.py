python
import time

def create_pattern():
    while True:
        # Generate random color pattern
        for i in range(256):
            color = chr((i * 16) % 256)
            print(f"\r{color}", end="")
            time.sleep(0.01)

create_pattern()

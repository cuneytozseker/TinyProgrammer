python
import time

def display_clock():
    while True:
        # Get the current time
        now = time.strftime("%H:%M:%S")
        
        # Print the clock on the console
        print(now)
        
        # Sleep for one second before updating the time again
        time.sleep(1)

# Start the clock
display_clock()

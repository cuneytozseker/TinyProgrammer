python
import time

def update_clock():
    while True:
        # Get current time as a string in 'HH:MM:SS' format
        now = time.strftime("%H:%M:%S")
        
        # Display the current time on the console
        print(now)
        
        # Wait for 1 second before updating again
        time.sleep(1)

# Run the function continuously
update_clock()

python
import time

def scroll_message(message, width):
    """
    Scrolls a message across the screen.
    
    :param message: The message to scroll.
    :param width: The width of the screen.
    """
    scroll_speed = 1
    offset = 0
    
    while True:
        # Print each character in the message one by one, moving the offset
        for char in message:
            print(char, end='')
            time.sleep(scroll_speed)
            
            # Move the scroll position to the right
            offset += scroll_speed
        
        # Reset the scroll position after a few steps
        time.sleep(0.1)
        
        # Check if the message has scrolled completely
        if offset >= len(message):
            break

# Example usage
message = "Welcome to the scrolling script!"
scroll_message(message, 80)

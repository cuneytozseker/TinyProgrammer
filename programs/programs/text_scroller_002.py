python
import time

def scroll_message(message, width):
    """
    Scrolls a message across the screen.

    Args:
    - message: The string to be scrolled.
    - width: The maximum width of the screen in characters.

    This function continuously scrolls the message across the screen until it reaches its end.
    """
    while True:
        # Scroll the message down
        print(message[-width:])
        time.sleep(0.1)  # Slightly delay to make scrolling smoother

# Example usage
scroll_message("Hello, World!", 80)
```

This script defines a function `scroll_message` that takes a string and its width as arguments. It continuously scrolls down the string using the `print()` function with the last `width` characters of the string. The `time.sleep(0.1)` ensures that each character is scrolled at a consistent rate, creating a smooth scrolling effect.
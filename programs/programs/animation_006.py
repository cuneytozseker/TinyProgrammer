python
import time

def draw_ascii_background():
    print("   _____")
    print("  |     |")
    print("  |     |")
    print("  |     |")

def draw_ascii_char(character):
    if character.isalpha():
        return f"{character.upper()}:"
    elif character.isdigit():
        return f"{character}"
    else:
        return ""

def create_ascii_animation():
    while True:
        draw_ascii_background()
        for i in range(10):  # Loop to create a 10x10 ASCII pattern
            print(draw_ascii_char(' '))
        time.sleep(1)
        print("   _____")
        print("  |     |")
        print("  |     |")

create_ascii_animation()

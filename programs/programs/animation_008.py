python
import time

def clear_canvas(c, r, g, b):
    c.clear(r, g, b)

def pixel(c, x, y, r, g, b):
    c.pixel(x, y, r, g, b)

def line(c, x1, y1, x2, y2, r, g, b):
    c.line(x1, y1, x2, y2, r, g, b)

def rect(c, x, y, w, h, r, g, b):
    c.rect(x, y, w, h, r, g, b)

def fill_rect(c, x, y, w, h, r, g, b):
    c.fill_rect(x, y, w, h, r, g, b)

def circle(c, x, y, radius, r, g, b):
    c.circle(x, y, radius, r, g, b)

def fill_circle(c, x, y, radius, r, g, b):
    c.fill_circle(x, y, radius, r, g, b)

def sleep(seconds):
    time.sleep(seconds)

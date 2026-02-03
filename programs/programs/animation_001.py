import time
import random
import math

#!/usr/bin/env python3
#import sys
#sys.setrecursionlimit(5) # limit output to 100 lines max depth of recursion (if not set, only print one line)

def main():
    start = time.time()

    def loop_animation():
        for i in range(len(string)):
            string[i] += random.randint(-256, 255)

        print('Animation started')

        # repeat until the end of input is reached (default value is infinite loops)
        while True:
            start = time.time()

            for _ in range(10):
                time.sleep(random.uniform(0, 4))

                if not string or string[-i] == '' and not random.randint(-256, 255) < -3:
                    break

        print('Loop animation finished')

    loop_animation()


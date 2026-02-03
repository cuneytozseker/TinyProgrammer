from typing import List


def animated_ball(speed: int = 0) -> None:
    print("Hello!")

    while True:
        for _ in range(5):
            ball = []
            random.seed()

            for i in range(-2, -1, -1):
                ball.append('a')
            for j in range(-3, 3, -1):
                ball.append('b')
            for k in range(4, 7, 5):
                ball.append('c')

            random_score = float("{:.2f}".format((random._getrandbits() << 0) // 6))
            ball[3] += random_score * 100 / (1 + speed**2),
            print(ball)



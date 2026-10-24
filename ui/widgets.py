WIN_W, WIN_H = 700, 580
WIRE_YS = [220 + 70 * i for i in range(5)]
BODY = (215, 40, 485, 540)
MONO = "Courier New"


def wire_geometry(n):
    if 0 <= n <= 4:
        return "left", WIRE_YS[n]
    return "right", WIRE_YS[n - 5]

import random

from config import (
    COLOR_RGB,
    FALLBACK_COLORS,
    N_WIRES,
    SERIAL_MIN_DIGITS,
    SERIAL_MAX_DIGITS,
    INSTRUCTIONS,
)

def new_serial():
    digits_count = random.randint(SERIAL_MIN_DIGITS, SERIAL_MAX_DIGITS)
    digits = "".join(random.choice("0123456789") for _ in range(digits_count))
    return "C-" + digits


def serial_digits(serial):
    return [int(ch) for ch in serial[2:]]


def mix_colors(a, b):
    ra, ga, ba = COLOR_RGB[a]
    rb, gb, bb = COLOR_RGB[b]
    return (min(ra + rb, 255), min(ga + gb, 255), min(ba + bb, 255))


def new_wires():
    numbers = list(range(N_WIRES))
    random.shuffle(numbers)
    color_names = list(COLOR_RGB.keys())
    available_count = random.randint(2, len(color_names))
    chosen_colors = random.sample(color_names, available_count)
    wires = []
    for idx, number in enumerate(numbers):
        color = chosen_colors[idx % available_count]
        wires.append({"number": number, "color": color})
    random.shuffle(wires)
    return wires


def pick_scenario():
    return random.choice(list(INSTRUCTIONS.keys()))


def _remaining(wires, cut):
    return [w for w in wires if w["number"] not in cut]


def _lowest_set(remaining):
    return {min(remaining, key=lambda w: w["number"])["number"]}


def _even_odd_allowed(digit, remaining):
    parity = digit % 2
    matching = {w["number"] for w in remaining if w["number"] % 2 == parity}
    if matching:
        return matching
    return _lowest_set(remaining)


def _remainder_sum(digits):
    return sum(digits) % 10


def _fallback_color_allowed(remaining, fallback_count):
    for step in range(len(FALLBACK_COLORS)):
        color = FALLBACK_COLORS[(fallback_count + step) % len(FALLBACK_COLORS)]
        matching = {w["number"] for w in remaining if w["color"] == color}
        if matching:
            return matching, fallback_count + 1
    return _lowest_set(remaining), fallback_count + 1


def _mixing_allowed(wires, cut, last_cut_number):
    remaining = _remaining(wires, cut)
    last_color = next(w["color"] for w in wires if w["number"] == last_cut_number)
    priority = [(255, 255, 255), (255, 0, 255), (0, 255, 255)]
    for target_rgb in priority:
        matching = {
            w["number"]
            for w in remaining
            if mix_colors(last_color, w["color"]) == target_rgb
        }
        if matching:
            return matching
    return _lowest_set(remaining)


def correct_cut(scenario, serial, wires, cut, fallback_count):
    digits = serial_digits(serial)
    remaining = _remaining(wires, cut)
    if not remaining:
        return set(), fallback_count

    cut_count = len(cut)
    total = len(digits)
    if cut_count >= total:
        return set(), fallback_count

    if scenario == "even_odd_right":
        digit = digits[total - 1 - cut_count]
        return _even_odd_allowed(digit, remaining), fallback_count

    if scenario == "even_odd_left":
        digit = digits[cut_count]
        return _even_odd_allowed(digit, remaining), fallback_count

    if scenario in ("remainder_last", "remainder_first"):
        working = digits[:]
        for _ in range(cut_count):
            if working:
                if scenario == "remainder_last":
                    working.pop()
                else:
                    working.pop(0)
        target_number = _remainder_sum(working)
        if any(w["number"] == target_number for w in remaining):
            return {target_number}, fallback_count
        return _fallback_color_allowed(remaining, fallback_count)

    if scenario == "mixing":
        if cut_count == 0:
            target_number = digits[-1]
            if any(w["number"] == target_number for w in remaining):
                return {target_number}, fallback_count
            return _lowest_set(remaining), fallback_count
        last_cut_number = cut[-1]
        return _mixing_allowed(wires, cut, last_cut_number), fallback_count

    return _lowest_set(remaining), fallback_count


def total_cuts_needed(serial):
    return len(serial_digits(serial))

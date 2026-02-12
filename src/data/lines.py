# -*- coding: utf-8 -*-

def get_A5_line_data(side):
    result = []
    start_y = 18.176
    gap = (73.680 - start_y) / 11
    step = start_y

    for i in range(3):
        if step != start_y:
            step += gap
        data = {"x": 10 if side == "left" else 17, "y": step, "w": 121, "th": 1}
        result.append(data)
        for j in range(11):
            step += gap
            data = {"x": 10 if side == "left" else 17, "y": step, "w": 121, "th": 0.333}
            result.append(data)

    step += gap
    result.append({"x": 10 if side == "left" else 17, "y": step, "w": 121, "th": 1})
    return result

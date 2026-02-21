# -*- coding: utf-8 -*-
"""
Each of the functions in this module returns a data structure that
represents the grid of lines to be drawn on each page of a planner.

The structure is:

```python
[
    {
        “ax”: <num>  # horizontal position of the first point
        “ay”: <num>  # vertical position of the first point
        "bx": <num>  # horizontal position of the second point
        "by": <num>  # vertical position of the second point
        “th”: <num>  # thickness of the line in typographic points
    }
]
```
"""


def get_A5_line_data(side):
    result = []
    start_y = 18.176
    gap = (73.680 - start_y) / 11
    step = start_y

    for i in range(3):
        if step != start_y:
            step += gap
        ax = 10 if side == "left" else 17
        ay = step
        bx = ax + 121
        by = step
        data = {"ax": ax, "ay": ay, "bx": bx, "by": by, "th": 1}
        result.append(data)
        for j in range(11):
            step += gap
            ax = 10 if side == "left" else 17
            ay = step
            bx = ax + 121
            by = step
            data = {"ax": ax, "ay": ay, "bx": bx, "by": by, "th": 0.333}
            result.append(data)

    step += gap
    ax = 10 if side == "left" else 17
    ay = step
    bx = ax + 121
    by = step
    result.append({"ax": ax, "ay": ay, "bx": bx, "by": by, "th": 1})
    # additional vertical line only on the right page
    if side == "right":
        result.append(
            {"ax": 77.5, "ay": 139.361, "bx": 77.5, "by": 139.361 + 60.639, "th": 0.333}
        )
    return result

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


def get_A5_1w2p_line_data(side):
    """
    Generates a structured list of line coordinates for an A5 layout in Scribus.

    The function calculates horizontal lines with varying thicknesses (1.0 for
    main markers and 0.333 for intermediate ones) and adds a specific vertical
    guide if the right page is requested.

    Args:
        side (str): The page side, either "left" or "right".

    Returns:
        list[dict]: A list of dictionaries, each containing:
            - 'ax', 'ay': Starting coordinates (x, y).
            - 'bx', 'by': Ending coordinates (x, y).
            - 'th': Line thickness (float).
    """
    result = []
    start_y, end_y = 18.176, 73.680
    gap = (end_y - start_y) / 11

    # Set fixed X coordinates based on page side
    ax = 10 if side == "left" else 17
    bx = ax + 121

    # Helper function to append line data to the result list
    def add_line(y, thickness):
        result.append({"ax": ax, "ay": y, "bx": bx, "by": y, "th": thickness})

    current_y = start_y

    # Main loop: 3 blocks consisting of 1 thick line followed by 11 thin lines
    for _ in range(3):
        add_line(current_y, 1)
        for _ in range(11):
            current_y += gap
            add_line(current_y, 0.333)
        current_y += gap  # Vertical spacing for the next block

    # Closing horizontal line
    add_line(current_y, 1)

    # Additional vertical guide only for the right-hand page
    if side == "right":
        result.append(
            {"ax": 77.5, "ay": 139.361, "bx": 77.5, "by": 139.361 + 60.639, "th": 0.333}
        )

    return result

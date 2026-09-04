# core/hints.py - Pedagogical Educational Hints for Cognitive Quest

def get_educational_hint(quarter_id, question_text, choices=None, correct_idx=None):
    """
    Returns a topic-specific educational hint to guide students when an answer is incorrect,
    reinforcing concepts without directly spoiling the answer.
    """
    q_lower = str(question_text).lower()

    # Quarter 1: 2D Shapes & Composite Figures
    if quarter_id == "quarter1":
        if "half" in q_lower and "circle" in q_lower:
            return "A whole circle cut straight in half gives two equal semicircles!"
        if "four equal parts" in q_lower or "quarter" in q_lower:
            return "When a whole is split into four equal parts, each individual piece is one quarter (1/4)!"
        if "house" in q_lower:
            return "Look for a shape that forms flat walls (square) and a shape for a peaked roof (triangle)!"
        if "without turning" in q_lower or "slide" in q_lower or "moved" in q_lower:
            return "A slide (translation) moves a shape in a direction without rotating or flipping it!"
        if "composite" in q_lower:
            return "A composite figure is made by joining two or more basic shapes together!"
        if "triangle" in q_lower:
            return "Count the edges and vertices: a triangle always has exactly 3 sides and 3 angles!"
        if "square" in q_lower or "rectangle" in q_lower:
            return "Squares have 4 equal sides; rectangles have opposite sides of equal length."
        return "Recall the properties of the shape and count its sides and equal parts!"

    # Quarter 2: Fractions, Money & Measurement
    elif quarter_id == "quarter2":
        if "fraction" in q_lower or "half" in q_lower or "fourth" in q_lower or "/" in q_lower:
            return "The bottom number (denominator) is the total equal parts; the top (numerator) is shaded parts."
        if "mango" in q_lower or "share" in q_lower or "equal" in q_lower:
            return "Divide the total count evenly among the recipients to find each person's share!"
        if "p" in q_lower or "peso" in q_lower or "coin" in q_lower or "bill" in q_lower or "change" in q_lower:
            return "Add the values of each coin or bill, then find the difference from the total price."
        if "meter" in q_lower or "perimeter" in q_lower or "length" in q_lower:
            return "Perimeter is the total boundary distance—add together the lengths of all outer sides."
        if "solid" in q_lower or "cube" in q_lower or "cylinder" in q_lower or "cone" in q_lower or "sphere" in q_lower:
            return "3D figures have volume: spheres are round, cylinders have circles on ends, cubes have square faces."
        return "Carefully check the numbers and units before selecting your answer!"

    # Quarter 3: Operations (Multiplication, Division, Time)
    elif quarter_id == "quarter3":
        if "multiply" in q_lower or "times" in q_lower or "product" in q_lower or "x" in q_lower:
            return "Multiplication is repeated addition of equal groups: 4 × 3 means 3 + 3 + 3 + 3!"
        if "divide" in q_lower or "quotient" in q_lower or "split" in q_lower:
            return "Think: what number multiplied by the divisor equals the starting number?"
        if "clock" in q_lower or "time" in q_lower or "hour" in q_lower or "minute" in q_lower:
            return "The short hand points to the hour, and each big number on the clock represents 5 minutes."
        if "day" in q_lower or "week" in q_lower or "month" in q_lower:
            return "Remember that there are 7 days in a week and 12 months in a calendar year."
        return "Break the problem down step-by-step into equal parts or repeated additions!"

    # Quarter 4: Data, Pictographs, Sequences & Logic
    elif quarter_id == "quarter4":
        if "graph" in q_lower or "chart" in q_lower or "bar" in q_lower:
            return "Look at the top edge of the bar and trace it over to the axis scale to read the exact number."
        if "pictograph" in q_lower or "key" in q_lower or "symbol" in q_lower:
            return "Check the legend/key at the bottom to see how many items each picture symbol represents!"
        if "pattern" in q_lower or "sequence" in q_lower or "next" in q_lower:
            return "Look at how much is added or subtracted between each step in the sequence."
        if "total" in q_lower or "how many" in q_lower:
            return "Sum up the values of each category carefully to get the overall total."
        return "Carefully review the graph or sequence to identify the pattern or highest value!"

    return "Take a deep breath, re-read the problem carefully, and think through each choice!"

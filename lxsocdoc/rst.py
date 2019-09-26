import textwrap

def make_table(t):
    """Make a reStructured Text Table

    Returns
    -------

    A string containing a reStructured Text table.
    """
    column_widths = []

    table = "\n"
    if len(t) <= 0:
        return table

    # Figure out how wide to make each column
    for col in t[0]:
        column_widths.append(0)

    for row in t:
        for i, column in enumerate(row):
            column_widths[i] = max(column_widths[i], len(column))

    # Print out header
    header = t.pop(0)
    table += "+"
    for i, column in enumerate(header):
        table += "-" + "-"*column_widths[i]
        table += "-+"
    table += "\n"

    table += "|"
    for i, column in enumerate(header):
        table += " " + column.ljust(column_widths[i]) + " |"
    table += "\n"

    table += "+"
    for i, column in enumerate(header):
        table += "=" + "="*column_widths[i]
        table += "=+"
    table += "\n"

    for row in t:
        table += "|"
        for i, column in enumerate(row):
            table += " " + column.ljust(column_widths[i]) + " |"
        table += "\n"

        table += "+"
        for i, column in enumerate(row):
            table += "-" + "-"*column_widths[i]
            table += "-+"
        table += "\n"
    table += "\n"

    return table

def print_table(table, stream):
    """Print a reStructured Text table

    Arguments
    ---------

    table (:obj:`list` of :obj:`list`s): A list of rows in the table.
    Each row has several columns.  The first row is the table header.

    stream (:obj:`io`): Destination output file.
    """
    column_widths = []

    print("", file=stream)
    if len(table) <= 0:
        return

    # Figure out how wide to make each column
    for col in table[0]:
        column_widths.append(0)

    for row in table:
        for i, column in enumerate(row):
            column_widths[i] = max(column_widths[i], len(column))

    # Print out header
    header = table.pop(0)
    print("+", file=stream, end="")
    for i, column in enumerate(header):
        print("-" + "-"*column_widths[i], file=stream, end="")
        print("-+", file=stream, end="")
    print("", file=stream)

    print("|", file=stream, end="")
    for i, column in enumerate(header):
        print(" " + column.ljust(column_widths[i]) + " |", file=stream, end="")
    print("", file=stream)

    print("+", file=stream, end="")
    for i, column in enumerate(header):
        print("=" + "="*column_widths[i], file=stream, end="")
        print("=+", file=stream, end="")
    print("", file=stream)

    for row in table:
        print("|", file=stream, end="")
        for i, column in enumerate(row):
            print(" " + column.ljust(column_widths[i]) + " |", file=stream, end="")
        print("", file=stream)

        print("+", file=stream, end="")
        for i, column in enumerate(row):
            print("-" + "-"*column_widths[i], file=stream, end="")
            print("-+", file=stream, end="")
        print("", file=stream)
    print("", file=stream)

def reflow(s, width=80):
    """Reflow the jagged text that gets generated as part
    of this Python comment.

    In this comment, the first line would be indented relative
    to the rest.  Additionally, the width of this block would
    be limited to the original text width.

    To reflow text, break it along \n\n, then dedent and reflow
    each line individually.

    Finally, append it to a new string to be returned.
    """
    out = []
    for piece in textwrap.dedent(s).split("\n\n"):
        trimmed_piece = textwrap.fill(textwrap.dedent(piece).strip(), width=width)
        out.append(trimmed_piece)
    return "\n\n".join(out)

def _reflow(s, width=80):
    return reflow(s, width)

def print_rst(stream, s, reflow=True):
    """Print a given string to the given stream.  Ensure it is reflowed."""
    print(_reflow(s), file=stream)
    print("", file=stream)
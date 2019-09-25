
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

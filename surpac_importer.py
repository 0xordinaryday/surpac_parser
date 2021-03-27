def process(input_line, new_segment, points, lines, polygons):
    splitline = input_line.strip().split(',')
    string_number = int(splitline[0])
    y = float(splitline[1])
    x = float(splitline[2])
    if string_number == 0:  # is a segment break
        if len(new_segment) == 1:
            new_key = len(points) + 1
            points[new_key] = new_segment
        elif new_segment[0] == new_segment[-1]:
            new_key = len(polygons) + 1
            polygons[new_key] = new_segment
        else:
            new_key = len(lines) + 1
            lines[new_key] = new_segment
        new_segment = []
    else:
        new_segment.append(splitline)


def get_file_length(filename):
    ''' returns number of lines in file '''
    with open(filename, 'r') as infile:
        return sum(1 for line in infile)


def main(filename):
    new_segment = []
    points = {}
    lines = {}
    polygons = {}
    file_length = get_file_length(filename)
    with open(filename, 'r') as infile:
        for index, line in enumerate(infile):
            if index + 1 < file_length and index > 1:
                process(line, new_segment, points, lines, polygons)
    return(points, lines, polygons)


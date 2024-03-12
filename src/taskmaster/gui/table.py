from ..utils.logger import logger


# Generate config table
def table(data):
    # Get the keys (column names) from the first row of data
    keys = []
    # Get all the keys of all the services
    for service in data:
        for key in service.keys():
            if key not in keys:
                keys.append(key)

    padding = 3

    # Calculate the maximum width for each column
    max_widths = [len(key) for key in keys]
    for row in data:
        for i, value in enumerate(row.values()):
            max_widths[i] = max(max_widths[i], len(str(value)))

    content = ""
    # Print the header
    for i, key in enumerate(keys):
        content += f"{key:<{max_widths[i] + padding}}".capitalize()
    content += "\n"
    # Print the data
    for row in data:
        for i, value in enumerate(row.values()):
            content += f"{str(value):<{max_widths[i] + padding}}"
        content += "\n"
    return content

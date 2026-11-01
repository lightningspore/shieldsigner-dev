"""Display NUL-bearing values without changing their underlying text."""
def display(value):
    return value.replace('\\','\\\\').replace('\0','\\0') if '\0' in value else value

def title(value,original):
    return original+' (\\0=NUL, \\\\=backslash)' if '\0' in value else original

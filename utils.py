"""
Miscellaneous utility functions.
"""

from collections import namedtuple

"""
Dataclass for a postcode found on a URL.
Stores the postcode, the URL, and the distance from a home postcode given elsewhere.
"""
Result = namedtuple('Result', ['pc', 'url', 'dist'])

def print_info(pc, dist, extra, indent=False):
    """Print the given postcode, distance and extra information in a set format.
    Optionally indent the line."""
    format_spec = "{:10s}{:6.0f}km\t{}"
    if indent:
        format_spec = "\t" + format_spec
    print(format_spec.format(pc, dist, extra))
        
def print_ascii(s):
    """ Given a string in a weird encoding, convert it to ASCII and print it."""
    print(s.encode('ascii', 'ignore').decode())
    
def strip_protocol(url):
    """Return the URL without a http/https header."""
    for prot in ['https://', 'http://']:
        if url.startswith(prot):
            return url[len(prot):]
    return url

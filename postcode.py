"""
Postcode/geographic-related functionality.
Use pc/pcs refers to postcode/postcodes.
"""

import re
import math
import pgeocode
import scrape

REGEX = '[A-Z]{1,2}[0-9][0-9A-Z]?\s?[0-9][A-Z][A-Z]'

def extract_from_string(s):
    """Search the given string for postcodes.
    Return a set of all postcodes found, converted to have spacing in the middle."""
    matches = re.findall(re.compile(REGEX), s)
    spaced = [add_spacing(x) for x in matches]
    return set(spaced)

def extract_from_url(url):
    """Return a set of all postcode strings found on the given URL."""
    strings = scrape.extract_visible_strings(url)
    pcs = set()
    for string in strings:
        pcs.update(extract_from_string(string))
    return pcs

def add_spacing(pc):
    """Add spacing in the middle to an otherwise valid postcode."""
    return pc if ' ' in pc else pc[:-3] + ' ' + pc[-3:]

def distance_between(a, b):
    """Return the distance between two postcodes in kilometers.
    Requires postcodes to have spacing in the middle.
    Return None on failure."""
    
    dist =  pgeocode.GeoDistance('GB').query_postal_code(a, b)
    if math.isnan(dist):
        return None
    return dist

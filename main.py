"""
Input some Google search terms.
Get a list of UK postcodes from the pages given by Google search results.
Use pc/pcs to refer to postcode/postcodes.
"""

import requests
import re
import json
import urllib.parse
import urllib.request
import pgeocode
import math
from itertools import chain
from bs4 import BeautifulSoup
from bs4.element import Comment
from collections import namedtuple

"""Dataclass for a postcode found on a URL.
Stores the postcode, the URL, and the distance from a home postcode given elsewhere."""
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

def add_spacing_to_pc(pc):
    """Add spacing in the middle to an otherwise valid postcode."""
    return pc if ' ' in pc else pc[:-3] + ' ' + pc[-3:]
    
def strip_protocol(url):
    """Return the URL without a http/https header."""
    for prot in ['https://', 'http://']:
        if url.startswith(prot):
            return url[len(prot):]
    return url
    
def urls_from_google_search(search_terms, page=1, ignore_subdomains=False):
    """Return a list of unique result links returned from a Google search of the given search terms.
    Optionally specify a results page.
    Optionally ignore any links that are subdomains of other links."""
    
    if not search_terms or page < 1: return None
    
    query_params = {}
    query_params['q'] = '+'.join(search_terms)
    query_params['start'] = (page - 1) * 10
    
    url = 'https://www.google.com/search?' + '&'.join(['{}={}'.format(x, y) for x, y in query_params.items()])
    
    links = []
    
    def hrefs_from_url(url):
        """Return a list of link hrefs found on the given url."""
        r = requests.get(url)
        soup = BeautifulSoup(r.content, from_encoding=r.encoding, features='html.parser')
        return [link['href'] for link in soup.find_all('a', href=True)]    
    
    for href in hrefs_from_url(url):
        """ We expect the href of results links to look like:
        '/url?q=https://www.example.com/subpage&sa=U&ved=0ahUKEwjFzLfz...'. """
        
        prefix = '/url?q=h'
        ignore = 'webcache.googleusercontent.com'
        
        if not href.startswith(prefix): continue
        if ignore in href: continue
            
        new_link = href[len(prefix)-1:]
        new_link = new_link.split('&')[0]
        new_link = urllib.parse.unquote(new_link)

        if new_link in links: continue
        
        if ignore_subdomains:
        
            def is_sublink_of(sublink, link):
                """Return True/False for whether the given sublink is actually a sublink of the given link."""
                if link.endswith('/'):
                    return sublink.startswith(link)
                else:
                    return sublink.startswith(link + '/')

            # Continue if new link is a subdomain of previous link
            if any([is_sublink_of(new_link, link) for link in links]): continue
                
            # Remove any previously added link if subdomain of new link
            links = [link for link in links if not is_sublink_of(link, new_link)]

        links.append(new_link)
        
    return links
      
def texts_from_url(url):
    """Return a list of visible strings from the given URL.
    Heavily copied from:
    https://stackoverflow.com/questions/1936466/beautifulsoup-grab-visible-webpage-text/1983219."""
    
    try:
        content = requests.get(url, timeout=3).content
    except requests.exceptions.ConnectionError:
        return []
    except requests.exceptions.ReadTimeout:
        return []

    soup = BeautifulSoup(content, 'html.parser')
    texts = soup.findAll(text=True)
    
    def tag_visible(element):
        if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
            return False
        if isinstance(element, Comment):
            return False
        return True
    
    visible_texts = filter(tag_visible, texts)
    stripped = [t.strip() for t in visible_texts]
    return [t for t in stripped if t]
        
def pcs_from_string(s):
    """Search the given string for postcodes.
    Return a set of all postcodes found, converted to have spacing in the middle."""
    regex = '[A-Z]{1,2}[0-9][0-9A-Z]?\s?[0-9][A-Z][A-Z]'
    matches = re.findall(re.compile(regex), s)
    spaced = [add_spacing_to_pc(x) for x in matches]
    return set(spaced)

def pcs_from_url(url):
    """Return a set of all postcode strings found on the given URL."""
    texts = texts_from_url(url)
    all_pcs = set()
    for text in texts:
        pcs = pcs_from_string(text)
        all_pcs.update(pcs)
    return all_pcs
    
def dist_between_pcs(a, b):
    """Return the distance between two postcodes in kilometers.
    Requires postcodes to have spacing in the middle.
    Return None on failure."""
    
    dist =  pgeocode.GeoDistance('GB').query_postal_code(a, b)
    if math.isnan(dist):
        return None
    return dist
    
def main():

    home_pc = add_spacing_to_pc('CB4 2FY')
    dist_limit = 20 # Measured in kilometers
    search_terms = ['parks', 'in', 'cambridge']
    
    # Keep track of good results and of all postcodes already seen
    results, pcs_seen = [], []
    
    urls = urls_from_google_search(search_terms)
    for count, url in enumerate(urls):
    
        print("\nScraping page {}/{} ({})...\n".format(count + 1, len(urls), strip_protocol(url)))
        
        for pc in pcs_from_url(url):
            if pc not in pcs_seen:
                pcs_seen.append(pc)
                dist = dist_between_pcs(pc, home_pc)
                if dist <= dist_limit:
                    print_info(pc, dist, 'in range', indent=True)
                    results.append(Result(pc, url, dist))
                else:
                    print_info(pc, dist, 'out of range', indent=True)

    print("Results:")
    for result in results:
        print_info(result.pc, result.dist, result.url)

            
if __name__ == '__main__':
    main()

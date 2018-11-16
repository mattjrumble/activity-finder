"""
Input some Google search terms.
Get a list of UK postcodes from the pages given by Google search results.
"""

import requests
import re
from itertools import chain
from bs4 import BeautifulSoup
from bs4.element import Comment
import urllib.parse


def print_ascii(s):
    """ Given a string in a weird encoding, convert it to ASCII and print it."""
    print(s.encode('ascii', 'ignore').decode())

def strip_protocol(url):
    """Return the URL without a http/https header."""
    for prot in ['https://', 'http://']:
        if url.startswith(prot):
            return url[len(prot):]
    return url
    
def links_from_google_search(search_terms, page=1, ignore_subdomains=False):
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
      
def texts_from_webpage(url):
    """Return a list of visible strings from the given URL.
    Heavily copied from:
    https://stackoverflow.com/questions/1936466/beautifulsoup-grab-visible-webpage-text/1983219."""
    
    try:
        content = requests.get(url, timeout=3).content
    except requests.exceptions.ConnectionError:
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
        
def postcodes_from_string(s):
    """Search the given string for postcodes.
    Return a set of all postcodes found, converted to have spacing in the middle."""
    regex = '[A-Z]{1,2}[0-9][0-9A-Z]?\s?[0-9][A-Z][A-Z]'
    matches = re.findall(re.compile(regex), s)
    return tidy_postcodes(matches)

def postcodes_from_webpage(url):
    """Return a set of all postcode strings found on the given URL."""
    texts = texts_from_webpage(url)
    all_postcodes = set()
    for text in texts:
        postcodes = postcodes_from_string(text)
        all_postcodes.update(postcodes)
    return all_postcodes
       
def tidy_postcodes(postcodes):
    """Convert a list of postcodes to have spacing in the middle, then remove duplicates by returning a set."""
    spaced = [(x if ' ' in x else x[:-3] + ' ' + x[-3:]) for x in postcodes]
    return set(spaced)
    
def main():

    search_terms = ['cambridge', 'swimming', 'pool']
    all_postcodes = set()
    
    for url in links_from_google_search(search_terms):
    
        print("Link: " + strip_protocol(url) + "...")
        postcodes = postcodes_from_webpage(url)

        for postcode in postcodes - all_postcodes:
            print("Postcode found: " + postcode)

        all_postcodes.update(postcodes)
        
    print("All postcodes: {}".format(all_postcodes))
            
if __name__ == '__main__':
    main()
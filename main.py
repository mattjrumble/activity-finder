"""
Input some Google search terms and a home address.
Get a list of nearby UK postcodes from the pages given by Google search results.
"""

from utils import print_info, strip_protocol, Result
from scrape import google_search_urls
import postcode

def main():

    home_pc = postcode.sanitize('CB4 2FY')
    dist_limit = 20 # Measured in kilometers
    search_terms = ['cambridge', 'supermarkets']

    # Keep track of good results and of all postcodes already seen
    results, pcs_seen = [], []

    urls = google_search_urls(search_terms)
    for count, url in enumerate(urls):

        print("\nScraping page {}/{} ({})...\n".format(count + 1, len(urls), strip_protocol(url)))

        for pc in postcode.extract_from_url(url):
            if pc not in pcs_seen:
                pcs_seen.append(pc)
                dist = postcode.distance_between(pc, home_pc)
                if not dist:
                    continue
                elif dist <= dist_limit:
                    print_info(pc, dist, 'in range', indent=True)
                    results.append(Result(pc, url, dist))
                else:
                    print_info(pc, dist, 'out of range', indent=True)

    print("Results:")
    for result in results:
        print_info(result.pc, result.dist, result.url)

if __name__ == '__main__':
    main()

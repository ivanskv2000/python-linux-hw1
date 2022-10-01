import requests
from requests.exceptions import InvalidSchema, Timeout, ConnectionError, RequestException
import shutil
from pathlib import Path
import os
from bs4 import BeautifulSoup
import time
import argparse
import urllib.parse
import itertools
import enlighten
from treelib import Tree
import click

# Define command line arguments
parser = argparse.ArgumentParser(
    description='Parse a website and save all html pages.',
    epilog='''
    By default, parser.py creates an url.txt file with page ids and their urls
    and a data folder with html contents of pages (<page id>.html).

    If -t option is enabled, tree.txt file is also created,
    which contains a tree representation of the website.
    '''
)
parser.add_argument(
    'url',
    metavar='URL',
    help="url of the site to parse",
    type=str
    )
parser.add_argument(
    '-d',
    '--depth',
    help="depth of search (default=2)",
    type=int,
    default=2
    )
parser.add_argument(
    '-n',
    help="maximum number of urls to parse (default=None)",
    type=int,
    default=None
    )
parser.add_argument(
    '-s',
    '--sleep',
    help="sleep time between requests (default=0)",
    type=float,
    default=0
    )
parser.add_argument(
    '-t',
    help='save a tree representation of the site (tree.txt)',
    default=False,
    action='store_true'
    )

# Parse arguments from the command line
args = parser.parse_args()
url = args.url
if (urllib.parse.urlsplit(url).scheme == '') or (urllib.parse.urlsplit(url).netloc == ''):
    raise ValueError(
        '''
        Incorrect url is provided.
        Please specify url in the format "<scheme>://<location>/<path>",
        e.g. "https://ru.wikipedia.org/"
        '''
        )
depth = args.depth
n_urls = args.n
sleep = args.sleep
return_tree = args.t

# Print info message
print('Parsing ' + url + ' ...')


# Define the parser class to initialise later
class DeepWebParser:
    def __init__(self, url, depth=2, n=None, sleep=0, path='./'):
        self.url = url                      # url to parse
        self.depth = depth                  # depth of search
        self.n = n                          # max number of urls
        self.c = itertools.count(start=1)   # document id counter
        self.path = path                    # path in which results are saved
        self.warns = []                     # warnings occured
        self.tree = []                      # data for site tree
        self.sleep = sleep                  # sleep time between requests

        # command line page counter
        counter_format = '{desc}{desc_pad}{count:d} {unit}{unit_pad} (press ctrl+c to interrupt){fill}[{elapsed}]'
        self.manager = enlighten.get_manager(width=60)
        self.id_counter = self.manager.counter(
            total=None,
            desc='Parsed',
            unit='pages',
            counter_format=counter_format
            )

    def complete_url(self, u, base):
        '''
        Return a correct representation of an url,
        for example if given url is relative.
        Requires a parent (base) url.
        '''

        base_scheme = urllib.parse.urlsplit(base).scheme
        base_netloc = urllib.parse.urlsplit(base).netloc
        base = base_scheme + '://' + base_netloc

        if (urllib.parse.urlsplit(u).netloc == ''):
            if '#' in u:
                return base + '/' + u
            else:
                return urllib.parse.urljoin(base, u)
        elif (urllib.parse.urlsplit(u).scheme == ''):
            return 'https:' + u
        else:
            return u

    def tree_search(self, url, depth, parent_id=None):
        '''
        Recursively parse the website.
        One call corresponds to one url.
        '''

        time.sleep(self.sleep)  # wait between iterations to prevent bans

        if depth > 0:
            id = str(next(self.c))              # generate next document id
            if self.n and int(id) > self.n:     # check condition for max. number of pages
                return

            # load page, accounting for `requests` package exceptions
            content = ''
            try:
                response = requests.get(
                    url,
                    headers=None
                    )
                content = response.text
            except (InvalidSchema, Timeout, ConnectionError) as req_err:
                self.warns.append(url + '\t' + str(req_err) + '\n')
            except RequestException:
                self.warns.append(url + '\t' + 'Unexpected error occured' + '\n')

            self.id_counter.update()            # update command line counter

            # save html contents of current page
            data_path = os.path.join(self.path, 'data', id+'.html')
            with open(data_path, 'w') as content_file:
                content_file.write(content)

            # append id and url to urls.txt
            with open(os.path.join(self.path, 'urls.txt'), 'a') as urls_file:
                urls_file.write(id + ' ' + url + '\n')

            # cooking a [very beautiful] soup
            soup = BeautifulSoup(content, 'html.parser')

            # retrieving page title
            if soup.find('title') is not None:
                title = soup.find('title').text
                title = title[:96]
            else:
                title = 'Unknown'
            title = title.strip()

            # working with fragment identifiers in urls ("#").
            # urls with different #'s are identical from the html point of view,
            # but are nevertheless saved separately with different titles.
            # Titles can be seen in tree.txt file if -t option is enabled.
            if '#' in url:
                title = title + ' (#' + url.split('#')[1] + ')'
            self.tree.append([title, id, parent_id])

            # retrieving all hyperrefs on page
            urls = soup.find_all('a')
            urls = [self.complete_url(i['href'], url) for i in urls if i.has_attr('href')]

            # removing "tel:" and "mailto:" links, which are pointless
            urls = [i for i in urls if ('tel:' not in i) and ('mailto:' not in i)]

            # filtering out self-links
            urls = list(filter(lambda x: x != url, urls))

            # removing duplicates
            urls = list(set(urls))

            # recursively call the function for each url on the page
            for u in urls:
                self.tree_search(url=u, depth=depth-1, parent_id=id)

        else:
            return

    def remove_files(self):
        '''
        Remove all data from parsing.
        '''
        data_dir = Path(os.path.join(self.path, 'data'))

        if data_dir.exists() and data_dir.is_dir():
            shutil.rmtree(data_dir)
        Path(os.path.join(self.path, 'urls.txt')).unlink(missing_ok=True)
        Path(os.path.join(self.path, 'tree.txt')).unlink(missing_ok=True)

    def end_cycle(self):
        '''
        Happily end the process.
        Ask if user wants to see the errors occured during parsing.
        '''
        if len(self.warns) == 0:
            print('\nHave a nice day!')
        elif click.confirm(f'\n\n{len(self.warns)} warnings occured. Want to see them?', default=True):
            print(*self.warns, sep='')
        else:
            print('\nHave a nice day!')

    def parse(self):
        '''
        Execute parsing process
        '''
        self.remove_files()
        Path(
            os.path.join(self.path, 'data')
            ).mkdir(parents=True, exist_ok=True)
        self.tree_search(self.url, self.depth)
        self.end_cycle()

    def save_tree(self):
        '''
        Save a tree representation of the website.
        '''
        tree = Tree()
        for node, id, parent in self.tree:
            tree.create_node(node, id, parent)

        tree.save2file(os.path.join(self.path, 'tree.txt'))


try:
    parser = DeepWebParser(
        url=url,
        depth=depth,
        n=n_urls,
        sleep=sleep
        )
    parser.parse()
except KeyboardInterrupt:
    parser.end_cycle()

if return_tree:
    parser.save_tree()

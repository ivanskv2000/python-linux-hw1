# Python and Linux &mdash; HW-1

![meme](https://user-images.githubusercontent.com/54892573/192755055-7f6dd303-b19c-4651-808b-000ed118e4b2.jpg)

## Description
This script parses a website up to a specified depth or number of pages.

By default, parser.py creates an url.txt file with page ids and their urls
and a data folder with html contents of pages (<page id>.html). If -t option is enabled, tree.txt file is also created,
which contains a tree representation of the website.

## Usage
### Step 1. Set Up the Working Environment
To isolate project execution, first create and activate a python virtual environment in the project directory:
``` bash
cd path_to_project/
python -m venv ./venv
source venv/bin/activate 
```

This enables you to install all required packages from `requirements.txt`:
``` bash
pip install -r requirements.txt
```

### Step 2. Run the Parser
To parse a website, run 
``` bash
python3 parser.py [-h] [-d DEPTH] [-n N] [-s SLEEP] [-t] URL
```
At its minimum, the script just requires a full url of a website to parse. The list of optional arguments can be retrieved via `python3 parser.py -h`. 
-  `-h, --help` show this help message and exit
-  `-d, --depth` depth of search (default=2)
-  `-n` maximum number of urls to parse (default=None)
-  `-s --sleep` sleep time between requests (default=0)
-  `-t` save a tree representation of the site (tree.txt) (default: False)

## Remarks
- The code in `parser.py` is heavily commented, please refer there for more info.
- Parser does not use any methods to bypass anti-parsing blockings. It is assumed that given sites are not protected from parsing. The only way to lower the risk of a server-side blocking is to specify the `sleep` parameter.
- It is possible to see the warnings for each requested url (if any) after the parsing is completed. To do so, print "Y" when prompted.
- Fragment identifiers ("#") in urls, which refer to page sections rather that other pages are treated as ordinary links. For example, urls "https://one.com/article#fragment_1" and "https://one.com/article#fragment_2" will generate two separate ids and two data files, even though these pages are identical from the html point of view. Of course, this behavior can be modified by changing the `DeepWebParser.complete_url()` function (split by "#" and drop the right-hand side part), but I thought it is better to keep the hashes as is.

## Example
> :warning: **Results may vary depending on your machine, network and other specifications.**

Let's parse the [Poetry website](https://python-poetry.org). We'll set the depth at 3 (without max. number of pages) and ask to save a tree representation of the site. Running
``` bash
python3 parser.py -d 3 -t "https://python-poetry.org"
```
we get 2081 pages in almost 23 minutes, and 3 warnings among them. Two of these warnings refer to websites that are blocked in Russia and therefore unreachable, and one is due to incorrect url.
```
https://www.patreon.com/	HTTPSConnectionPool(host='www.patreon.com', port=443): Max retries exceeded with url: / (Caused by SSLError(SSLEOFError(8, 'EOF occurred in violation of protocol (_ssl.c:1129)')))
https://twitter.com/vercel	HTTPSConnectionPool(host='twitter.com', port=443): Max retries exceeded with url: /vercel (Caused by NewConnectionError('<urllib3.connection.HTTPSConnection object at 0x7fecb27cd790>: Failed to establish a new connection: [Errno 60] Operation timed out'))
9https://github.com/python-poetry/poetry/pull/4942	No connection adapters were found for '9https://github.com/python-poetry/poetry/pull/4942'
```
Last url is indeed broken, you can find it [here](https://python-poetry.org/history/) (lookup for `<a href="9https://github.com/python-poetry/poetry/pull/4942">#4942</a>` in html code).

`urls.txt` file is a log of all urls that were visited by the parser:
```
1 https://python-poetry.org
2 https://python-poetry.org/docs/plugins/
3 https://python-poetry.org/blog/
4 https://python-poetry.org//docs/pyproject/#plugins
5 https://python-poetry.org/docs/configuration/
...
```

`data` directory contains html dumps of all the pages listed in `urls.txt`. We also get a tree representation of the Poetry website (see below).

https://github.com/ivanskv2000/python-linux-hw1/blob/dc04db6153bcab92908e41272522b797f32f6ee5/example_tree.txt#L1-L100
 
What's interesting here:
- Fragment identifiers ("#") are indeed parsed as separate pages, e. g. "Commands | Documentation | Poetry - Python dependency management and packaging made easy (#install)", where (#install) refers to the name of the fragment.
- We can clearly see three levels of this website, since we set the `depth` parameter at 3.
- Duplicated links are only removed within one page and not globally, so naturally we see the Blog page several times in our tree (Poetry -> Basic Usage -> Blog, Poetry -> Blog, etc.)


 

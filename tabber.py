import re
import requests
import sys

from bs4 import BeautifulSoup


def find_pagination(srch):
    '''Send GET request for a search.

    Returns:
        String containing the search results from UG (partly written in JSON)
        ^fix this

    '''

    srch = srch.replace(' ', '%20')

    url = f'https://www.ultimate-guitar.com/search.php?search_type=title&value={srch}'

    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")

    res = soup.find_all('div')[-1]

    s = str(res)
    # tabs = re.search(r'(?<="results":)[^*]*', s)

    tabs = re.search(r'(?<=results)[^*]*', s)

    s = s.replace('&quot;', '"')

    end_keyword = 'pagination'
    search_end = re.search(f',"{end_keyword}', s)
    end_idx = search_end.span()[0]

    tabs = s[:end_idx]

    return tabs


def create_dict(tabstring):
    ''' Create dictionary containing info about a tab.

    Args:
        
    Returns:
        List of dictionaries st. each dictionary
            contains info about a search result from UG
    '''

    def relevant(s, irrelevant_types = ['Bass Tabs', 'Video', 'Pro', 'Ukulele']):
        '''
        Args:
            Types that are not relevant/interesting/allowed
        
        Returns:
            False if the tabstring is irrelevant, True if relevant
        '''
        for t in irrelevant_types:
            if t in s:
                return False
        
        return True

    tab = re.finditer(r'"id":', tabstring)
    taburl = re.finditer(r'"tab_url":', tabstring)

    idx = []
    d = []

    for t in tab:
        idx0 = t.span()[0]
        idx.append(idx0)
    
    for i, index in enumerate(idx[:-1]):
        tabstring_i = tabstring[index:idx[i+1]]

        tabstring_i = '{' + tabstring_i[:-2]

        tabstring_i = tabstring_i.replace('null', 'None')
        tabstring_i = tabstring_i.replace('true', 'True')
        tabstring_i = tabstring_i.replace('false', 'False')

        # Check whether the tabstring is relevant/interesting:
        if not relevant(tabstring_i):
            continue

        try:
            tab_d = eval(tabstring_i)
        except SyntaxError:     # Error that I refuse to attempt tackling
            continue

        d.append(tab_d)

    return d

def choose_tab(tabdict, ask_input = True, with_song_titles = True):
    ''' Print the search results at Ultimate Guitar as a table.

    Args:
        tabdict: List of tab dictionaries
        ask_input: If True, the user selects a tab. If False, the 0th one is selected.
    
    Returns:
        Dictionary containing info about chosen tab (ie. one of the tabdict elements)
    '''
    print(f'INDEX \t\t VOTES \t RATING\t TYPE')

    for i, d in enumerate(tabdict):
        print(f'{i} \t\t {d["votes"]} \t {d["rating"]:.2f} \t {d["type"]:10} \t', end='')
        if with_song_titles:
            print(f'{d["artist_name"]:30} {d["song_name"]}')
        else:
            print('')
    
    if ask_input:
        # Ask user to select a search result:
        index = input('> ')
        index = int(index)

        if index > len(tabdict):
            raise IndexError('Not a valid index!')
    
        return tabdict[index]
    else:
        # Return the first search result (which is usually the best one):
        return tabdict[0]

def dict_from_search(srch):
    ''' Print the search results from Ultimate Guitar as a table and ask
    user to select between the results.

    Args:
        serch: A search (as string) for Ultimate Guitar GET request

    Returns:
        Dictionary for chosen search result

    '''

    tabs = find_pagination(srch)
    d = create_dict(tabs)
    d = choose_tab(d, ask_input = True)

    return d


def url_from_dict(d):
    '''
    Args:
        d: dictionary for tab
    
    Returns:
        URL of the tab
    '''
    return d['tab_url']


def fetch_tab(url):
    ''' 
    Args:
        url: Url of tab on UG

    Returns:
        The text containing the tabs from the URL
    '''

    # Scrape:
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")

    res = soup.body.find('div', class_='js-store')
    res = str(res)


    capo_pattern = re.escape("capo&quot;:") + r'(\d+),'
    capo_match = re.search(capo_pattern, res)

    # Use regex to find start and end of tab text:
    T_start = re.search(r'(?<=wiki_tab)[^*]', res) # to match wiki_tab in the string
    T_end = re.search(r'(?<=revision_id)[^*]', res) # to match revision_id in the string

    # Corresponding indices:
    idx = [T_start.span()[0], T_end.span()[0]]

    # Resulting plain text (not yet readable):
    text = res[idx[0]:idx[1]]

    # Clean up the plain text (very messy):
    if 'chords' not in url:

        for_replacing = [
            '":{"content":"',
            '","revision_id'
        ]
    elif 'chords' in url:

        for_replacing = [
            '&quot;:{&quot;content&quot;:&quot;',
            '&quot;,&quot;revision_id'
        ]

    for s in for_replacing:
        text = text.replace(s, '')

    if capo_match:
        text = f"Capo at fret {capo_match.group(1)}\n\n" + text

    return text


def prettify_tabs(text):
    '''Make text from UG into readable plain text'''
    text = text.replace('\\r', '')
    text = text.replace('\\n', '\n')

    for_replacing = ['[tab]', '[/tab]', '[ch]', '[/ch]']
    for s in for_replacing:
        text = text.replace(s, '')

    return text


def write_tab_to_file(d, custom_filename=False):
    '''Write tab to text file.
    
    Args:
        d: dictionary for chosen search result
        custom_filename: custom filename if desirable
    '''

    text = fetch_tab(url_from_dict(d))
    text = prettify_tabs(text)

    if custom_filename:
        filename = custom_filename + '.txt'
    else:
        filename = f"{d['artist_name']}_{d['song_name']}_{d['type']}_v{d['version']}.txt"
    
    print(f'\n\n\nWriting to file {filename}.txt')

    with open(filename, 'w') as outfile:
        outfile.write(text)

def display_tabs(d):
    ''' Prints the plain text in the tab/chord on UG.

    Args:
        d: dictionary for a chosen search result
    '''
    text = fetch_tab(url_from_dict(d))  # Get tab as text
    text = prettify_tabs(text)          # Make text readable

    print(text)


# Join command line arguments to form a search:
srch = sys.argv[1:]
srch = ' '.join(srch)


# Check if flag:
if '-w' in srch:
    p = re.compile('-w')
    beg, en = p.search(srch).span()

    if en != len(srch):
        filename = srch[en+1:]  # Custom filename
    else:
        filename = False

    file = True
    srch = srch[:beg-1] # Remove flag from search
else: 
    file = False

    
d = dict_from_search(srch)  # Print table of srch results
display_tabs(d)             # Display chosen tab

if file: write_tab_to_file(d, filename)

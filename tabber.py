import re
import requests
import sys

from bs4 import BeautifulSoup


def find_pagination(srch):
    '''Send GET request for a search.

    Returns:
        String containing the search results from UG (partly written in JSON)
    '''

    srch = srch.replace(' ', '%20')

    url = f'https://www.ultimate-guitar.com/search.php?search_type=title&value={srch}'

    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")

    res = soup.find_all("div")[-1]

    s = str(res)

    tabs = re.search(r'(?<=results)[^*]*', s)

    s = s.replace("&quot;", '"')

    end_keyword = "pagination"
    search_end = re.search(f',"{end_keyword}', s)
    end_idx = search_end.span()[0]

    tabs = s[:end_idx]

    return tabs


def create_dict(tabstring):
    ''' Create dictionaries containing info about the search results that correspond to relevant tabs/chords.

    Args:
        tabstring: string returned from find_pagination
        
    Returns:
        list of python dictionaries st. each dictionary contains info about a result in tabstring
    '''

    def relevant(s, irrelevant_types = ["Bass Tabs", "Video", "Pro", "Ukulele"]):
        '''
        Args:
            s: string corresponding to regex match, see below
            irrelevant_types: types that are not relevant/interesting/allowed
        
        Returns:
            False if the tabstring is irrelevant, True if relevant
        '''
        # return False for s that do not correspond to a valid chord or tab:
        if "song_id" not in s: return False

        # return False for s that are in irrelevant_types:
        for t in irrelevant_types:
            if t in s:
                return False
        
        return True

    tab = re.finditer(r'"id":', tabstring)

    idx = []
    d = []

    for t in tab:
        idx0 = t.span()[0]
        idx.append(idx0)

    # the following loops through the starting indices (denoted index) of each result (denoted i) in tab,
    # parses the string corresponding to result i so that it becomes a valid python dictionary
    # (with special treatment for the parsing of the endpoint),
    # asserts whether the python dictionary corresponds to an actual tab/chord result AND is not an "irrelevant type" (see above),
    # and adds valid & relevant dictionaries to the list d
    for i, index in enumerate(idx):
        tabstring_i = tabstring[index:] if i == len(idx) - 1 else tabstring[index:idx[i+1]]

        tabstring_i = "{" + tabstring_i[:-2]
        if i == len(idx) - 1: tabstring_i = tabstring_i + "}"

        tabstring_i = tabstring_i.replace('null', 'None')
        tabstring_i = tabstring_i.replace('true', 'True')
        tabstring_i = tabstring_i.replace('false', 'False')

        # check whether the tabstring is relevant/interesting:
        if not relevant(tabstring_i):
            continue

        try:
            tab_d = eval(tabstring_i)
        except SyntaxError:     # error that I refuse to attempt tackling
            continue

        d.append(tab_d)

    return d

def choose_tab(tabdict, with_song_titles = True):
    ''' Print the search results at Ultimate Guitar as a table.

    Args:
        tabdict: list of tab dictionaries
    
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

    # ask user to select a search result:
    index = input("> ")
    index = int(index)

    if index > len(tabdict):
        raise IndexError("Not a valid index.")
    
    return tabdict[index]

def dict_from_search(srch, chosen_index = None):
    ''' Print the search results from Ultimate Guitar as a table and ask
    user to select between the results.

    Args:
        srch: a search (as string) for Ultimate Guitar GET request
        chosen_index: either None or integer-valued. if False, the user selects a result index. if integer-valued, corresponding index is automatically chosen

    Returns:
        Dictionary for chosen search result

    '''

    tabs = find_pagination(srch)
    d = create_dict(tabs)
    if chosen_index:
        d = d[int(chosen_index)]
    else:
        d = choose_tab(d)

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
        url: url of tab on UG

    Returns:
        The text containing the tabs from the URL
    '''

    # scrape:
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")

    res = soup.body.find("div", class_="js-store")
    res = str(res)

    capo_pattern = re.escape("capo&quot;:") + r'(\d+),'
    capo_match = re.search(capo_pattern, res)

    # obtain tuning:
    tuning_pattern = re.escape("tuning&quot;:") + r'\{[^\}]*'
    tuning_match = re.search(tuning_pattern, res)
    if tuning_match:
        tuning_str = tuning_match.group(0)
        tuning_idx = tuning_str.find("&quot;value&quot;:&quot;") + len("&quot;value&quot;:&quot;")
        tuning = tuning_str[tuning_idx:]
        tuning = tuning[:tuning.find("&")]
    else:
        tuning = "E A D G B E"

    # use regex to find start and end of tab text:
    t_start = re.search(r'(?<=wiki_tab)[^*]', res) # to match wiki_tab in the string
    t_end = re.search(r'(?<=revision_id)[^*]', res) # to match revision_id in the string

    # corresponding indices:
    idx = [t_start.span()[0], t_end.span()[0]]

    # resulting plain text (not yet readable):
    text = res[idx[0]:idx[1]]

    # clean up the plain text:
    for_replacing = [
        '&quot;:{&quot;content&quot;:&quot;',
        '&quot;,&quot;revision_id',
        '":{"content":"',
        '","revision_id'
    ]

    for s in for_replacing:
        text = text.replace(s, '')

    if capo_match:
        text = f"Capo: {capo_match.group(1)}\n\n" + text

    if tuning != "E A D G B E":
        text = f"Tuning: {tuning}\n" + text

    return text


def prettify_tabs(text):
    '''Make text from UG into readable plain text'''
    text = text.replace("\\r", "")
    text = text.replace("\\n", "\n")

    for_replacing = ["[tab]", "[/tab]", "[ch]", "[/ch]"]
    for s in for_replacing:
        text = text.replace(s, "")

    return text

def write_tab_to_file(d, custom_filename = False):
    '''Write tab to text file.
    
    Args:
        d: dictionary for chosen search result
        custom_filename: custom filename if desirable
    '''

    text = fetch_tab(url_from_dict(d))
    text = prettify_tabs(text)

    if custom_filename:
        filename = custom_filename + ".txt"
    else:
        filename = f'{d["artist_name"]}_{d["song_name"]}_{d["type"]}_v{d["version"]}.txt'
    
    print(f"- - -\n\n\nWriting to file {filename}")

    with open(filename, "w") as outfile:
        outfile.write(text)

def display_tabs(d):
    ''' Prints the plain text in the tab/chord on UG.

    Args:
        d: dictionary for a chosen search result
    '''
    text = fetch_tab(url_from_dict(d))  # get tab as text
    text = prettify_tabs(text)          # make text readable

    print(text)


if __name__ == "__main__":
    # join command line arguments to form a search:
    srch_raw = sys.argv[1:]
    srch = srch_raw

    if "-w" in srch_raw:
        srch = srch_raw[0:srch_raw.index("-w")]
    if "-s" in srch:
        srch = srch[0:srch.index("-s")]

    # messy code for fetching flags and arguments thereof:
    
    srch = " ".join(srch)

    flags = ["-w", "-s"]
    flag_provided = []
    flags_result = []

    # the following assumes the arguments accompanying the 
    # flags are one-worded (which is reasonable for filenames and integers):
    for f in flags:
        if f in srch_raw:
            flag_provided.append(True)

            idx = srch_raw.index(f)
            argument_provided = idx + 1 < len(srch_raw)
            if argument_provided:
                argument_provided = srch_raw[idx + 1] not in flags

            if argument_provided:
                flags_result.append(srch_raw[idx + 1])
            else:
                flags_result.append(None)
        else:
            flag_provided.append(False)
            flags_result.append(None)

        
    d = dict_from_search(srch, chosen_index = flags_result[1])  # print table of srch results
    display_tabs(d)             # display chosen tab

    if flag_provided[0]: write_tab_to_file(d, custom_filename = flags_result[0])

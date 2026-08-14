# Tabscraper
Python code for scraping the search results and chords/tabs off Ultimate Guitar.

The user provides a search as a command line argument, which is used in a GET request to Ultimate Guitar. A table of the search results is printed to the terminal, and the user then selects the tab they want from the result table. Lastly, the tab is printed as plain text to the terminal.

Very ugly spagetti code, but it works, and you can stay away from all the flashing autoplays and ads on Ultimate Guitar. 

Information about capo and tuning is provided (if these are "non-trivial", i.e. other than 0, EADGBE respectively).

## Usage:
```
python tabber.py blah blah
```
or, to write the tab to a text file `filename.txt`,
```
python tabber.py blah blah -w filename
```
where a suited filename is chosen if filename is omitted.

For example: `python tabber.py queens of the stone age no one knows -w`.

If you want to pre-select an index in the aforementioned result table, add flag `-s index` where index is an integer. For example, `-s 0` is useful.


![Animation displaying procedure for fetching a tab/chord](assets/tabscraper_demo.gif)

## To do:
* Bass + ukulele players
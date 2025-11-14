# Tabscraper
Python code for scraping the search results and chords/tabs off Ultimate Guitar.

The user provides a search as a command line argument, which is used in a GET request to Ultimate Guitar. A table of the search results is printed to the terminal, and the user then selects the tab they want. Lastly, the tab is printed as plain text to the terminal.

Very ugly spagetti code, but it works, and you can stay away from all the flashing autoplays and ads on Ultimate Guitar.

## Usage:
```
python tabber.py blah blah
```
or, to write the tab to a text file `filename.txt`,
```
python tabber.py blah blah -w filename
```
where a suited filename is chosen if filename is omitted.

Ex `python tabber.py queens of the stone age no one knows -w`


![Animation displaying procedure for fetching a tab/chord](assets/tabscraper_demo.gif)

## To do:
* Add info about tuning
* Comments
* Bass + ukulele players
# sparse
Parsing engine and utilities for the data from sociation.org.

Use the following commands in interactive mode:

dbbuild - builds the database initially, parsing all words and their links from the website.
dbrebuild - updates the existing database automatically.
webstat - lists total numbers of the words on the website.
dbstat - prints words/links in db.

quit - quits the utility.

-expert-commands- # tasks could be re-/started manually (in case of break or error on some step)

dbparseweb - saves words from the website to db.
dblink - saves links, parsing the website / better when initial words parsing was complete.
dbrelink - saves links in safe mode / better for relinking incomplete database.
dbcleanup - detects and removes dead words (with no links - misspelled, unmoderated).
  
-export-

exportcsvnum - exports links db with a position number for each word charachter.
exportcsvid - exports links db with an id for each word.
exportcsvtxt - exports links db with a plain text words. #needs unicode fix to stop crashin in win
  

# -*- coding: utf-8 -*-
from __future__ import print_function
__author__ = 'buzzroll'

import console_unicode
import requests
import urllib
from bs4 import BeautifulSoup
import sys
import datetime
import os
import sqlite3



basedir = os.path.abspath(os.path.dirname(__file__))
DATABASE_URI = os.path.join(basedir, 'sparse.db')


try:
    db = sqlite3.connect(DATABASE_URI)
    cursor = db.cursor()
    cursor.execute("PRAGMA cache_size = 65536")
    cursor.execute('''CREATE TABLE IF NOT EXISTS word(id INTEGER PRIMARY KEY NOT NULL UNIQUE, word varchar(64) NOT NULL UNIQUE, links INTEGER, updated DATETIME)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS relation(id INTEGER PRIMARY KEY NOT NULL UNIQUE, word_id INTEGER, rate_to INTEGER, rate_from INTEGER, related_word_id INTEGER,
                      updated DATETIME, FOREIGN KEY(word_id) REFERENCES word(id), FOREIGN KEY(related_word_id) REFERENCES word(id))''')
    cursor.execute('''CREATE UNIQUE INDEX IF NOT EXISTS rel_index ON relation(word_id,related_word_id)''')
    db.commit()
except Exception as e:
    db.rollback()
    raise e



root_url = 'http://sociation.org/'

letters = [u'А', u'Б', u'В', u'Г', u'Д', u'Е', u'Ё',
           u'Ж', u'З', u'И', u'Й', u'К', u'Л', u'М',
           u'Н', u'О', u'П', u'Р', u'С', u'Т', u'У',
           u'Ф', u'Х', u'Ц', u'Ч', u'Ш', u'Щ', u'Ы',
           u'Э', u'Ю', u'Я']

ABC = [u'А', u'Б', u'В', u'Г', u'Д', u'Е', u'Ё',
           u'Ж', u'З', u'И', u'Й', u'К', u'Л', u'М',
           u'Н', u'О', u'П', u'Р', u'С', u'Т', u'У',
           u'Ф', u'Х', u'Ц', u'Ч', u'Ш', u'Щ', u'Ъ',
           u'Ы', u'Ь', u'Э', u'Ю', u'Я', u' ', u'-', u"'"]



def warning(*objs):
    with open("sparse.log", "a") as text_file:
        print("{} >> WARNING: {}".format(datetime.datetime.today(),''.join(str(i) for i in objs)), file=text_file)
    print("WARNING: ", *objs, file=sys.stderr)

def log(*objs):
    with open("sparse.log", "a") as text_file:
        print("{} >> INFO: {}".format(datetime.datetime.today(),''.join(str(i) for i in objs)), file=text_file)
    print("INFO: ", *objs, file=sys.stderr)


def word_by_id(word_id):
    try:
        return cursor.execute('''SELECT word FROM word WHERE id=?''', (word_id,)).fetchone()[0]
    except TypeError as e:
        warning('target absent: %s /' % word_id , e)


def id_by_word(word):
    try:
        return cursor.execute('''SELECT id FROM word WHERE word=?''', (word,)).fetchone()[0]
    except TypeError as e:
        pass
        # warning('target absent: %s /' % word, e)


def get_totalpages(letter):
    links = []
    lastpage = 1
    view = requests.request('GET', ''.join([root_url, 'words/', letter, '/']))
    soup = BeautifulSoup(view.content, "html.parser")
    for link in soup.find_all('a'):
        links.append(link.get('href'))

    for x in xrange(len(links)):
        if (str(links[x]).find(u'?page=') != -1):
            if str(links[x+1]).find(u'?page=') != -1:
                lastpage = int(str(links[x]).strip(u'?page='))

    return lastpage


def get_totalwords(letter):
    lastpage = get_totalpages(letter)
    words_number = (20*(lastpage - 1) + len(get_words(letter, lastpage)))
    print ('Processing:', '[', letter, ']', 'Found:', words_number, 'words in', lastpage, 'pages.')
    return words_number


def get_words(letter, page):
    links = []
    words = []
    view = requests.request('GET', ''.join([root_url, 'words/', letter, '/', u'?page=', str(page)]))
    soup = BeautifulSoup(view.content)
    for link in soup.find_all('a'):
        links.append(link.get('href'))

    for x in xrange(len(links)):
        if (str(links[x]).find(u'/word/') != -1) and (urllib.unquote(str(links[x]).strip('/word/'))) not in words:
            words.append(urllib.unquote(str(links[x]).strip('/word/')))

    return words


def parse_word(word):
    wordslist = []
    found = True
    view = requests.request('GET', ''.join([root_url, 'word/', word, '/']))
    soup = BeautifulSoup(view.content)
    page = str(soup.find_all('div', class_= "text")).split('\n')

    print ('Processing associations for: [ %s ]' % word)

    if '404' in page[1]:
        found = False
        print('Was not found in internets. :(')

    else:
        for x in xrange(len(page)):
            if str(page[x]).rfind('</a>') != -1:
                link = (str(page[x]).split(': ')[-1]).rstrip('</a>').split('">')
                wordslist.append(link)

    for i in xrange(len(wordslist)):
        (wordslist[i].reverse())

    if found:
        print ('Found %s associations:\n'
               % len(wordslist), (' '.join(wordslist[x-1][0] if x % 15 != 0 else '\n' for x in xrange(len(wordslist)+1))),'\n')

    return wordslist


def db_save_word(word, logging=False):
    try:
        w_id = id_by_word(word.decode('utf-8'))
        if w_id != None:
            print('[ %s ] already exists, omitted.' % word)
            pass
        else:
            cursor.execute('''INSERT OR REPLACE INTO word(word, updated) VALUES (?,?)''', (word.decode('utf-8'), datetime.datetime.today()))
            if logging:
                log('Saved new word: %s' % id_by_word(word.decode('utf-8')))
    except Exception as e:
        warning(e)


def parse_all_to_db(logging=False):
    for letter in letters:
        lastpage = get_totalpages(letter)
        get_totalwords(letter)
        for page in xrange(1, lastpage+1):
            words = get_words(letter, page)
            print ('Processing: page %s of  %s / found %s words on page:\n%s\n'
                   % (page, lastpage, len(words), ' '.join(words[x-1] if x % 15 != 0 else '\n' for x in xrange(len(words)+1))))
            for word in words:
                db_save_word(word, logging=logging)
            print('\n Page checked.\n')

            db.commit()


def get_global_wordscount():
    total = 0
    for letter in letters:
        total += get_totalwords(letter)
    print ('\n', total, 'words in', len(letters), 'letters total.')


def if_link_exists(word_id, related_word_id):
    try:
        return ((cursor.execute('''SELECT count() FROM relation WHERE word_id=? AND related_word_id=?''',(word_id, related_word_id)).fetchone()[0]) != 0)
    except Exception as e:
        warning(e)


def db_save_link(word_id, rate_to, rate_from, related_word_id, check=True, logging=False):
    if check:
        try:
            validate_link = if_link_exists(word_id, related_word_id)
            if validate_link:
                current_rate_to, current_rate_from = cursor.execute('''SELECT rate_to, rate_from FROM relation WHERE word_id=? AND related_word_id=?''',(word_id, related_word_id)).fetchone()
                if current_rate_to != rate_to or current_rate_from != rate_from:
                    if current_rate_to != rate_to:
                        print('Link [ %s -> %s ] already exists, rating changed from %s to %s' % (word_by_id(word_id), word_by_id(related_word_id), current_rate_to, rate_to))
                        if logging:
                            log('Updated link rating for [ %s -> %s ] from %s to %s' % (word_id, related_word_id, current_rate_to, rate_to))
                        cursor.execute('''UPDATE relation SET rate_to = ? WHERE word_id = ? AND related_word_id = ?''', (rate_to, word_id, related_word_id))
                    else:
                        pass
                    if current_rate_from != rate_from:
                        print('Link [ %s <- %s ] already exists, rating changed from %s to %s' % (word_by_id(word_id), word_by_id(related_word_id), current_rate_from, rate_from))
                        if logging:
                            log('Updated link rating for [ %s <- %s ] from %s to %s' % (word_id, related_word_id, current_rate_from, rate_from))
                        cursor.execute('''UPDATE relation SET rate_from = ? WHERE word_id = ? AND related_word_id = ?''', (rate_from, word_id, related_word_id))
                    else:
                        pass
                else:
                    print('Link [ %s <-> %s ] already exists, rating is intact, omitted.' % (word_by_id(word_id), word_by_id(related_word_id)))
            else:
                try:
                    word = word_by_id(word_id)
                    related_word = word_by_id(related_word_id)
                    cursor.execute('''INSERT INTO relation(word_id, rate_to, rate_from, related_word_id, updated) VALUES (?,?,?,?,?)''',
                                   (word_id, rate_to, rate_from, related_word_id, datetime.datetime.today()))
                    print('Linked: %s <- %s - %s -> %s' % (word, rate_to, rate_from, related_word))
                    if logging:
                        log('New link [ %s <- %s - %s -> %s ] saved.' % (word_id, rate_to, rate_from, related_word_id))
                except Exception as e:
                    warning(e)

        except Exception as e:
            warning(e)
            pass
    else:
        try:
            word = word_by_id(word_id)
            related_word = word_by_id(related_word_id)
            cursor.execute('''INSERT INTO relation(word_id, rate_to, rate_from, related_word_id, updated) VALUES (?,?,?,?,?)''',
                           (word_id, rate_to, rate_from, related_word_id, datetime.datetime.today()))
            print('Linked: %s <- %s - %s -> %s' % (word, rate_to, rate_from, related_word))
        except Exception as e:
            warning(e)


def update_links_count(word):
    try:
        word_id = id_by_word(word)
        links = (cursor.execute('''SELECT count() FROM relation WHERE word_id=?''', (word_id,)).fetchone()[0])
        cursor.execute('''UPDATE word SET links = ? WHERE id = ?''', (links, word_id))
        print('\nChecked: %s link(s).\n' % links)
        db.commit()
    except Exception as e:
        warning(e)


def link_words(check=True, logging=True):
    for word_id, word in cursor.execute('''SELECT id, word FROM word''').fetchall():
        for link, rate in parse_word(word):
            related_word_id = id_by_word(link.decode('utf-8'))
            if related_word_id != None:
                db_save_link(word_id, int(rate.split('/')[0]), int(rate.split('/')[1]), related_word_id, check=check, logging=logging)
            else:
                print('%s is not present in DB, skipping.' % link[0])

        update_links_count(word)


def return_words_db(word, numbers=False, ids=False):
    wordlist = []
    try:
        word_id = cursor.execute('''SELECT id FROM word WHERE word=?''', (word,)).fetchone()[0]
        links = cursor.execute('''SELECT related_word_id, rate_to, rate_from FROM relation WHERE word_id=?''',(word_id,)).fetchall()
        print('Found: %s links for [ %s ]\n' % (len(links),word))
        for link_id, rate_to, rate_from in links:
            link = cursor.execute('''SELECT word FROM word WHERE id=?''', (link_id,)).fetchone()[0]
            if numbers:
                wordlist.append((''.join(str(ABC.index(l.upper())+1) for l in word),
                                 rate_to, rate_from, ''.join(str(ABC.index(l.upper())+1) for l in link)))
            elif ids:
                wordlist.append((id_by_word(word), rate_to, rate_from, link_id))
            else:
                wordlist.append((word, rate_to, rate_from, link))
    except Exception as e:
        warning('return_words_db() [ %s ]' % e)
    return wordlist


def db_cleanup(autoremove=False):
    deadlinks = cursor.execute('''SELECT * FROM word WHERE links IS NULL OR links = 0''', ).fetchall()
    print('DB cleanup complete. Found %s dead words.' % len(deadlinks))
    cursor.execute('''SELECT * FROM word WHERE links IS NULL OR links = 0''', )
    if len(deadlinks) == 0:
        print('Nothing to cleanup.')
        return None
    else:
        if autoremove:
            for id, word, links, date in deadlinks:
                print('Removed: %s %s' % (id, word))
                cursor.execute('''DELETE FROM word WHERE links IS NULL OR links = 0''', )
        else:
            prompt = True
            delete = raw_input('Remove dead words (with no links)? [Y/N]\n').decode('utf-8')
            while prompt:
                if delete == 'N':
                    break
                elif delete == 'Y':
                    for id, word, links, date in deadlinks:
                        print('Removed: %s %s' % (id, word))
                        cursor.execute('''DELETE FROM word WHERE links IS NULL OR links = 0''', )
                        prompt = False
                else:
                    delete = raw_input('Wrong command. Available [Y/N]\n').decode('utf-8')

    db.commit()


def build_db(rebuild=False, autocleanup=True):
    get_global_wordscount()
    parse_all_to_db(logging=rebuild)
    link_words(check=rebuild, logging=rebuild)
    db_cleanup(autoremove=autocleanup)
    print('\nDB building complete. %s words were saved to DB in %s links.' % ((cursor.execute('''SELECT count() FROM word''', ).fetchone())[0],
                                                                        (cursor.execute('''SELECT count() FROM relation''', ).fetchone())[0]))
def db_all_words():
    return db.execute('''SELECT word FROM word''',)


def db_export(numbers=False, ids=False):
    if numbers:
        fname = "db_export_num.csv"
    elif ids:
        fname = "db_export_id.csv"
    else:
        fname = "db_export_txt.csv"
    with open(fname, "w") as f:
        for w in db_all_words():
            words = return_words_db(w[0], numbers=numbers, ids=ids)
            for word, rate_to, rate_from, related_word in sorted(words, reverse=True):
                print(', '.join((str(word), str(rate_to), str(rate_from), str(related_word))), file=f)
    print('Wrote dump to: db_export.csv')

def main():
    run = True
    print('\nLoaded %s words in %s links.' % ((cursor.execute('''SELECT count() FROM word''', ).fetchone())[0],
                                                                    (cursor.execute('''SELECT count() FROM relation''', ).fetchone())[0]))
    while run:
        print('\nEnter word to find or a command to execute:\n')
        word = raw_input().decode('utf-8')
        if word == 'quit':
            run = False
        elif word == 'dbbuild':
            build_db(autocleanup=False)
        elif word == 'dbrebuild':
            build_db(rebuild=True, autocleanup=False)
        elif word == 'webstat':
            get_global_wordscount()
        elif word == 'dbstat':
            print('\n%s words in %s links.\n' % ((cursor.execute('''SELECT count() FROM word''', ).fetchone())[0],
                                                                        (cursor.execute('''SELECT count() FROM relation''', ).fetchone())[0]))
        elif word == 'dbparseweb':
            parse_all_to_db()
        elif word == 'dblink':
            link_words(check=False, logging=False)
        elif word == 'dbrelink':
            link_words()
        elif word == 'dbcleanup':
            db_cleanup(autoremove=False)
        elif word == 'exportcsvnum':
            db_export(numbers=True)
        elif word == 'exportcsvid':
            db_export(ids=True)
        elif word == 'exportcsvtxt':
            db_export()
        else:
            words = return_words_db(word)
            if len(words) == 0:
                print('Nothing found in DB. :(\nAsking sociation.ru...')
                parse_word(word)
            else:
                for word, rate_to, rate_from, w in sorted(words, reverse=True):
                    print(word, rate_to, rate_from, w)
    db.close()



if __name__ == '__main__':
  main()



#TODO: fix encoding exception in txt export
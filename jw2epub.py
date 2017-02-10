#!/usr/bin/env python3
# vim: set fileencoding=utf-8
"""Jungle World 2 EPUB

Download an issue of Jungle World and convert it to epub.
"""
__docformat__ = "epytext en"
import datetime
import logging
import os
import re
import shutil
import sys
from urllib import request
from http import client
from bs4 import BeautifulSoup
from epubaker import Epub3, File, Joint, Section
from epubaker.metas import (
    Title, Language, Identifier, Creator, Contributor, Publisher, get_dcterm)
from epubaker.tools import w3c_utc_date


VERSION = '0.1'

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)



class Settings(object):
    """Settings for running jw2epub"""
    CACHEDIR = 'cache'
    SERVER = 'https://jungle-world.com'
    URI_INDEX = '/inhalt/'
    URI_ARTICLE = '/artikel/'



class JW2EPUB(object):
    """Download an issue of Jungle World + prepare for conversion to epub"""
    def __init__(self, settings, issue_no=None):
        self.settings = settings

        if not os.path.exists(self.settings.CACHEDIR):
            os.mkdir(self.settings.CACHEDIR)

        if issue_no:
            self.issue_no = issue_no
            self.uri_index = '{}{}/'.format(
                self.settings.URI_ARTICLE,
                issue_no.replace('.', '/'),
            )
        else:
            self.issue_no = 'unknown'
            self.uri_index = self.settings.URI_INDEX

        self.issue_dir = os.path.join(self.settings.CACHEDIR, self.issue_no)
        self.title = 'Unknown issue of Jungle World'
        self.uri_cover = ''

        # Not sure if this actually works, do not have a working login atm
        if hasattr(self.settings, 'USER') and self.settings.USER and\
            hasattr(self.settings, 'PASSWORD') and self.settings.PASSWORD:
            passman = request.HTTPPasswordMgrWithDefaultRealm()
            passman.add_password(
                None,
                self.settings.SERVER,
                self.settings.USER,
                self.settings.PASSWORD)
            authhandler = request.HTTPBasicAuthHandler(passman)
            opener = request.build_opener(authhandler)
            request.install_opener(opener)


    def _fetch_html_file(self, filename):
        """Fetch HTML from cached file.

        @param filename: name of file to load from
        @type filename: str
        @return: fetched HTML
        @rtype: str
        """
        LOGGER.info('Fetch from file %s ...', filename)
        with open(filename, 'r', encoding='utf-8') as handle:
            html = handle.read()
        return html


    def _fetch_html_url(self, url):
        """Fetch HTML from live URL.

        @param url: url to load from
        @type url: str
        @return: fetched HTML
        @rtype: str
        """
        LOGGER.info('Fetch from url %s ...', url)
        try:
            return request.urlopen(url).read().decode()
        except client.BadStatusLine as err:
            LOGGER.warning('Failed fetching: %s', err)
            return None


    def _shall_skip_html(self, html):
        """Skip HTML (story) under certain conditions:

        - None
        - story not published yet

        @param html: HTML checked to be skipped
        @type html: str
        @return: if story shall be skipped
        @rtype: bool
        """
        if not html:
            return True

        prefix = 'Skip HTML'
        skip_text = 'Diesen Artikel finden Sie bisher nur in der gedruckten Jungle World'
        if skip_text in html:
            LOGGER.warning('%s: story not yet published.', prefix)
            return True

        return False


    def _fetch_html(self, uri, is_index=False):
        """Fetch HTML from either an existing cache dir or the internet.

        The index page is always fetched from the internet.

        @param uri: URI to fetch
        @type uri: str
        @param is_index: if uri is the index page
        @type is_index: bool
        @return: fetched HTML or None
        @rtype: str
        """
        cachedir = self.settings.CACHEDIR
        if is_index:
            filename = os.path.join(cachedir, 'index.html')
        else:
            basename = os.path.basename(uri)
            filename = os.path.join(self.issue_dir, basename)

        # always fetch index from url
        if not is_index and os.path.exists(filename):
            html = self._fetch_html_file(filename)
        else:
            html = self._fetch_html_url(self.settings.SERVER + uri)
            if self._shall_skip_html(html):
                return None
            else: # write to cache file
                LOGGER.info('Write to cache file %s', filename)
                with open(filename, 'w', encoding='utf-8') as handle:
                    handle.write(html)

        return html


    def parse_index(self):
        """Parse index file.

        Populates member variables issue_no, title, and uri_cover.
        Copies index file to issue dir.
        Return index soup.

        @return: soup of the index file
        @rtype: BeautifulSoup
        """
        cachedir = self.settings.CACHEDIR
        index = self._fetch_html(self.uri_index, True)
        soup = BeautifulSoup(index, 'html.parser')

        div = soup.find('div', attrs={'class':'cover_thumb'})
        self.title = div.find('p').text

        # e.g. title == 'Jungle World Nr. 31/12,2. August 2012'
        issue = self.title.split('.')[1:2][0].split(',')[0].strip().split('/')
        # issue is not prefixed with century
        century = str(datetime.datetime.now().year)[:2]
        self.issue_no = century + issue[1] + '.' + issue[0]
        self.issue_dir = os.path.join(cachedir, self.issue_no)
        if not os.path.exists(self.issue_dir):
            os.makedirs(self.issue_dir)
        shutil.move(
            os.path.join(cachedir, 'index.html'),
            os.path.join(self.issue_dir, 'index.html')
        )

        img_src = dict(div.find('img').attrs)['src']
        self.uri_cover = img_src.replace('thumb_', '')

        LOGGER.info(
            'META info: title %s, issue_no %s uri_cover %s',
            self.title,
            self.issue_no,
            self.uri_cover
        )
        return soup


    def get_story(self, uri):
        """Get one story / article from given URI.

        @param uri: URI of story
        @type uri: str
        @return: story
        @rtype: {'uri': str, 'head': str, 'html': str}
        """
        # possibly links to other issues
        if not uri.endswith('.html'):
            return None
        if self.issue_no.replace('.', '/') not in uri:
            return None

        html = self._fetch_html(uri)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')
        story = soup.find('div', attrs={'class':'story'})

        try: # add class chapter for e.g. automatic calibre TOC generation
            story.find('h1').attrs.append(('class', 'chapter'))
        except AttributeError:
            pass

        try: # remove print button
            story.find('div', {'class': 'menuR'}).extract()
        except AttributeError:
            pass

        try: # remove share buttons
            story.find('p', {'class': 'share'}).extract()
        except AttributeError:
            pass

        if story:
            output = {
                'uri': uri,
                'title': story.find('h1').find('span').text,
                'html': '<html><body>{}</body></html'.format(str(story))
            }
            return output
        else:
            return None


    def get_stories(self, soup):
        """Get all stories of current issue.

        @param soup: soup of index page to check for links to stories
        @type soup: BeautifulSoup
        @return: all stories of current issue.
        @rtype: []
        """
        regex = re.compile('/artikel')
        first = True
        stories = []
        parsed = []

        LOGGER.info('Get stories ...')
        for anchor in soup.findAll('a', attrs={'href':regex}):
            if first:
                first = False
                continue

            try:
                uri = dict(anchor.attrs)['href']
            except IndexError:
                continue

            if uri not in parsed:
                story = self.get_story(uri)
                if story:
                    stories.append(story)
                    parsed.append(uri)

        return stories


    def download_cover(self):
        """Download the cover image."""
        filename = os.path.join(
            self.issue_dir,
            os.path.basename(self.uri_cover)
        )
        LOGGER.info('Download cover image ...')
        request.urlretrieve(self.settings.SERVER + self.uri_cover, filename)
        return filename


    def make_book(self, stories):
        """Make an ebook out of the parsed stories.

        @param stories: stories of this issue
        @type stories: as returned by get_stories
        @return: resulting epub book
        @rtype: Epub3

        """
        LOGGER.info('Make ebook ...')
        book = Epub3()

        LOGGER.info('Add metadata ...')
        book_title = 'Jungle World {}'.format(self.issue_no)
        book.metadata.append(Title(book_title))
        book.metadata.append(Identifier(book_title))
        book.metadata.append(Language('de'))
        book.metadata.append(Creator('Redaktion Jungle World'))
        book.metadata.append(Publisher('Jungle World Verlags GmbH'))
        book.metadata.append(Contributor('jw2epub'))
        book.metadata.append(get_dcterm('modified')(w3c_utc_date()))

        LOGGER.info('Add cover image ...')
        filename_cover = self.download_cover()
        # Might be jpg or gif, but epub lib barfs at that extension
        book.files['cover.png'] = File(open(filename_cover, 'rb').read())
        book.cover_image = 'cover.png'

        for story in stories:
            LOGGER.info('Add story %s ...', story['title'])
            page = os.path.basename(story['uri'])
            book.files[page] = File(story['html'].encode('utf-8'))
            book.spine.append(Joint(page))
            book.toc.append(Section(story['title'], page))

        return book


    def run(self):
        """Run this method when using this class."""
        index = self.parse_index()
        stories = self.get_stories(index)
        book = self.make_book(stories)
        filename_book = 'JW-{}.epub'.format(self.issue_no)
        LOGGER.info('Write to %s', filename_book)
        book.write(filename_book)



if __name__ == "__main__":
    print('.oOo. Welcome to JW2EPUB version %s .oOo.' % VERSION)

    if len(sys.argv) > 1:
        issue_no = sys.argv[1]
    else:
        issue_no = None # current issue

    try:
        import settings
    except ImportError:
        settings = Settings()
    JW2EPUB(settings, issue_no).run()

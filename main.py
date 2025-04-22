import os
from bs4 import BeautifulSoup
from ebooklib import epub

folder = 'volume_01'
book_title = 'Volume 1'

book = epub.EpubBook()
book.set_identifier('volume1')
book.set_title(book_title)
book.set_language('en')
book.add_author('Constituent Assembly of India')  # or leave blank

chapters = []
toc = []

def get_content(soup: BeautifulSoup):
    # Extract the main content from the soup object
    content = soup.find('div', class_='content')
    if content:
        return str(content)
    return ''

# Sort files by date
files = sorted(os.listdir(folder), key=lambda f: f.lower())

for filename in files:
    if not filename.endswith('.html'):
        continue

    filepath = os.path.join(folder, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'lxml')

    date_title = filename.replace('.html', '')
    chapter_title = f"Debate on {date_title}"

    # Create chapter
    chapter = epub.EpubHtml(title=chapter_title, lang='en', file_name=filename)
    chapter.set_content(get_content(soup))
    book.add_item(chapter)
    chapters.append(chapter)

    # Extract subsection links for TOC
    subsections = []
    for tag in soup.find_all(['h2', 'h3']):
        if tag.has_attr('id'):
            subsection = epub.Link(f'{filename}#{tag["id"]}', tag.get_text(), tag["id"])
            subsections.append(subsection)

    if subsections:
        toc.append((epub.Link(filename, chapter_title, filename), subsections))
    else:
        toc.append(epub.Link(filename, chapter_title, filename))

# Generate spine and TOC
book.toc = toc
book.spine = ['nav'] + chapters

# Required EPUB items
book.add_item(epub.EpubNcx())
book.add_item(epub.EpubNav())

# Write EPUB
epub.write_epub('volume_1.epub', book)

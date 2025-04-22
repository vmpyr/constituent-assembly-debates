import os
from bs4 import BeautifulSoup, element
from ebooklib import epub
from datetime import datetime

def is_num(s):
    try:
        int(s)
        return True
    except:
        return False

def format_date(date_str):
    dt = datetime.strptime(date_str, '%d-%b-%Y')

    day = dt.day
    suffix = 'th' if 11 <= day <= 13 else {1:'st', 2:'nd', 3:'rd'}.get(day % 10, 'th')
    day_with_suffix = f"{day}{suffix}"

    return f"{day_with_suffix} {dt.strftime('%B %Y')}", dt

def get_sorted_file_list(folder):
    file_dict = {}
    file_list = os.listdir(folder)
    for file in file_list:
        if file.endswith('.html'):
            date_str = file.split('.')[0]
            file_dict[format_date(date_str)[1]] = file

    sorted_files = sorted(file_dict.items(), key=lambda x: x[0])
    return [file for _, file in sorted_files]

class BookDataPoint:
    def __init__(self, div_element: element.Tag, return_id: str):
        self.div_element = div_element
        self.return_id = return_id
        self.content = self._get_content()

    def _get_content(self):
        elements = self.div_element.find_all(['p', 'span'])
        added_id = False
        last_p_idx = None
        for i, el in enumerate(elements):
            if el.name == 'p':
                last_p_idx = i
                if not added_id and self.return_id != '':
                    el['id'] = self.return_id
                    added_id = True

            if el.name == 'span':
                el.attrs.pop('style', None)
                el.attrs.pop('class', None)
                el.string = el.get_text().upper()
                el.attrs = {'style': 'font-weight: bold'}

        if last_p_idx is not None:
            elements[last_p_idx].attrs['style'] = elements[last_p_idx].attrs.get('style', '') + ' margin-bottom: 2em;'

        return ''.join(str(el) for el in elements)


    def return_content(self):
        return self.content

def get_cleaned_content(soup: BeautifulSoup):
    links_ul = soup.find('ul', class_='links')
    if links_ul is None:
        relevant_ids = []
        relevant_titles = []
    else:
        relevant_ids = [a['href'] for a in links_ul.find_all('a', href=True)]
        relevant_ids = [link.split('#')[1] for link in relevant_ids if '#' in link]
        relevant_titles = [a.get_text() for a in links_ul.find_all('a', href=True)]

    relevant_divs = soup.find_all('div', id=True)
    relevant_divs = [div for div in relevant_divs if is_num(div['id'])]

    return_content = ""

    for div in relevant_divs:
        if div['id'] not in relevant_ids:
            return_content += BookDataPoint(div, "").return_content()
        else:
            return_content += BookDataPoint(div, div['id']).return_content()

    return return_content, iter(relevant_titles)

def bookify(folder: str, volume):
    """
    Converts a folder of HTML files into an EPUB book.
    """
    book_title = f'Constituent Assembly Debates - Volume {volume}'

    book = epub.EpubBook()
    book.set_identifier(f'Volume_{volume}')
    book.set_title(book_title)
    book.set_language('en')
    book.add_author('Constituent Assembly of India')
    book.add_metadata('DC', 'publisher', 'ConstitutionofIndia.net')
    book.add_metadata('DC', 'date', '1950-01-26')
    book.add_metadata(None, 'meta', '', {'name': 'calibre:series', 'content': 'Constituent Assembly Debates'})
    book.add_metadata(None, 'meta', '', {'name': 'calibre:series_index', 'content': str(int(volume))})
    tags = ['Constitution', 'India', 'History', 'Politics', 'Law']
    for tag in tags:
        book.add_metadata('DC', 'subject', tag)

    cover_image_name = f'volume_{volume}.png'
    with open(f'./cover_images/{cover_image_name}', 'rb') as img_file:
        image_item = epub.EpubItem(uid="cover-image", file_name=cover_image_name,
                                   media_type="image/png", content=img_file.read())
    book.add_item(image_item)
    cover_page = epub.EpubHtml(title='Cover', file_name='cover.xhtml', lang='en')
    cover_page.id = 'cover'
    cover_page.content = f'''
        <html xmlns="http://www.w3.org/1999/xhtml">
        <head><title>Cover</title></head>
        <body style="text-align:center; margin:0;">
            <img src="{cover_image_name}" alt="Cover Image" style="width:100%; height:auto;"/>
        </body>
        </html>
    '''
    book.add_item(cover_page)

    chapters = []
    toc = []

    file_list = get_sorted_file_list(folder)
    for filename in file_list:
        filepath = os.path.join(folder, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        date_title = format_date(filename.split('.')[0])[0]
        clean_title = date_title.replace(' ', '_')
        linking_file_name = f"file_{clean_title}.xhtml"
        chapter_title = f"{date_title}"

        chapter = epub.EpubHtml(title=chapter_title, lang='en', file_name=linking_file_name)
        parsed_content, subsection_titles = get_cleaned_content(soup)
        chapter.set_content(parsed_content)
        book.add_item(chapter)
        chapters.append(chapter)

        subsections = []
        soup = BeautifulSoup(parsed_content, 'html.parser')
        for tag in soup.find_all(['p']):
            if tag.has_attr('id'):
                subsection = epub.Link(f'{linking_file_name}#{tag["id"]}', next(subsection_titles), f"id_{tag["id"]}")
                subsections.append(subsection)

        if subsections:
            toc.append((epub.Link(linking_file_name, chapter_title, linking_file_name), subsections))
        else:
            toc.append(epub.Link(linking_file_name, chapter_title, linking_file_name))

    book.toc = toc
    book.spine = ['cover', 'nav'] + chapters

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    epub.write_epub(f'./books/Constituent Assembly Debates - Volume_{volume}.epub', book)

if __name__ == '__main__':
    for i in range(1, 13):
        if i < 10: volume = f'0{i}'
        else: volume = str(i)
        folder = f'./volumes/volume_{volume}'
        if os.path.exists(folder):
            bookify(folder, volume)
            print(f"Volume {volume} processed successfully.")

"""Получение данных из сохраненных страниц.

Получаем дату и время сохранения страницы.
Адрес, по которому расположена страница.
Заголовок страницы."""
import re

from dateutil import parser as dp
from lxml import etree
from lxml import html
from lxml.html.clean import Cleaner


def get_page_text_content(content):
    """Получает текстовое содержимое html-страницы.

    Parameters
    ----------
    content: str
        html-code страницы
    """
    cleaner = Cleaner(style=True)
    doc = html.document_fromstring(content)
    doc = cleaner.clean_html(doc)
    text = ' '.join(doc.xpath('//text()'))
    text = re.sub('\n', ' ', text)
    text = re.sub(' {2,}', ' ', text)
    return text


def get_data_from_page(page):
    """Получает данные из веб страницы.

    Урл расположения страницы, название статьи и дату сохранения копии страницы.

    Args:
        page (str): Html page file path.
    """
    Parser = etree.HTMLParser(encoding='utf-8')
    root = html.parse(page, parser=Parser).getroot()  # type root: lxml.etree.ElementTree

    # 'head' tag
    title = root.xpath('.//title/text()')[0].strip()

    # 'comment' parsing
    # get page url
    for i in root[0].text.strip().split('\n'):
        i = i.strip()
        if i.startswith('info'):
            url, saved_date = re.findall(r'\((.+?)\)', i)
        if i.startswith('url'):
            url = i.split(': ')[-1]
        elif i.startswith('saved date:'):
            saved_date = i.strip()
            saved_date = re.search(r'^.+: ([^G]+) G.+', saved_date)
            saved_date = dp.parse(saved_date.group(1))
            saved_date = saved_date.strftime('%Y-%m-%d %H:%M:%S')
    return title, url, saved_date


if __name__ == '__main__':
    import sys
    data = get_data_from_page(sys.argv[1])
    print(data)

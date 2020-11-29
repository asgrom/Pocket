"""Предоставляет методы для получения данных о сохранненых статьях с сервиса getpocket.com"""
import webbrowser
from . import applogger

from pocket import Pocket, PocketException

from . import CONSUMER_KEY, ACCESS_TOKEN

logger = applogger.get_logger(__name__)


# @pyqtSlot()
# def create_tag_tables(self):
#     """Создание таблиц tag и webpageTags в базе данных.
#
#     Метод используется только если база создается из Pocket сервиса.
#     Данные берутся с сервиса Pocket."""
#     pocket_data = get_pocket_data()
#     articles_lst = pocket_data['list']
#     cur = self.con.cursor()
#     try:
#         for article_data in articles_lst.values():
#             url = article_data.get('given_url')
#             tags = article_data.get('tags')
#             if not tags:
#                 continue
#             for tag in tags:
#                 tag_id = add_tag(tag, cur)
#                 add_page_tag(url, tag_id, cur)
#     except Exception:
#         logger.exception('Ошибка создания таблицы тегов')
#         QMessageBox.critical(self, 'Ошибка', 'Ошибка создания таблицы тегов')
#     finally:
#         cur.execute('commit')
#         cur.close()

def open_articles_in_browser(data: dict):
    """Открывает страницы из Pocket

    В описании каждой статьи сохранен урл, по которому она находится. Метод
    открывает их в браузере по 5 штук, чтобы их можно было сохранить.

    Args:
        data (dict):
    """
    i = 0
    for article in data['list'].values():
        webbrowser.open_new_tab(article['given_url'])
        i += 1
        if i == 5:
            i = 0
            input('Press any key')


def get_pocket_data(since=None, state=None, tag=None):
    """Получить json данные с getpocket

    Данные о сохраненных страницах в Pocket. tag - можно задать для поиска
    статей по определенному тегу.

    Args:
        since:
        state:
        tag:
    """
    try:
        p = Pocket(consumer_key=CONSUMER_KEY, access_token=ACCESS_TOKEN)
        return p.retrieve(since=since, state=state, tag=tag, detailType='complete')
    except PocketException:
        logger.exception('Exception get_pocket_data')

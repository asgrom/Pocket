"""Предоставляет методы для работы с sqlite базой"""
import re
import sqlite3 as sql
import sys
import traceback

from . import DATABASE
from . import applogger

logger = applogger.get_logger(__name__)


class SqliteError(Exception):
    pass


def close_connection(conn: sql.Connection):
    if conn:
        conn.close()
    sys.exit()


def connect(db: str = None) -> sql.Connection:
    """Создает и возвращает соединение с базой данных

    База данных берется из 'DATABASE'"""
    try:
        if not db:
            conn = sql.connect(DATABASE)
        else:
            conn = sql.connect(db)
        import os
        dirname = os.path.dirname(os.path.realpath(__file__))
        # загрузка расширения для регистронезависимого поиска по базе
        # noinspection PyUnresolvedReferences
        conn.enable_load_extension(True)
        # noinspection PyUnresolvedReferences
        conn.load_extension(os.path.join(dirname, 'sqlite_ext/libSqliteIcu.so'))
        # noinspection PyUnresolvedReferences
        conn.load_extension(os.path.join(dirname, 'sqlite_ext/fts5.so'))
        conn.executescript("pragma foreign_keys=on;")
        create_tables(conn)
        return conn
    except sql.Error:
        logger.exception('Exception in connect to dbase')
        sys.exit()


def export_tags_table(con: sql.Connection):
    tags_list = list()
    for tag in con.execute('select tag from tags;'):
        tags_list.append({'tag': tag[0]})
    return tags_list


def export_webpagetags_table(con: sql.Connection):
    request = """
        select title, tag, url from webpages join
        (select tag, id_page from tags join 
            webpagetags where tags.id = webpagetags.id_tag)
        where webpages.id = id_page order by title;"""
    table_list = list()
    for title, tag, url in con.execute(request):
        table_list.append({'title': title, 'tag': tag, 'url': url})
    return table_list


def drop_tables(connector: sql.Connection):
    """Удаление всех таблиц в базе данных"""
    try:
        connector.executescript(
            """
            pragma foreign_keys=off;
            begin transaction;
            drop table if exists webpages;
            drop table if exists tags;
            drop table if exists webpagetags;
            drop table if exists webcontents;
            commit;
            pragma foreign_keys=on;
            """
        )
    except sql.Error:
        logger.exception('Exception in drop tables')
        connector.rollback()
        close_connection(connector)


def create_tables(connector: sql.Connection):
    """Создание таблиц в базе данных

    Если в базе уже существуют таблицы, то они удаляются и создаются снова."""
    try:
        with connector:
            connector.executescript(
                """
                create table if not exists 'webpages' (
                id integer primary key autoincrement,
                'title' text,
                'url' text not null unique,
                'time_saved' text,
                'content' text
                );
                create table if not exists 'tags' (
                'id' integer primary key autoincrement,
                'tag' text unique not null
                );
                create table if not exists 'webpagetags'(
                'id' integer primary key autoincrement,
                'id_page' integer,
                'id_tag' integer,
                unique (id_page, id_tag),
                constraint fk_id_page foreign key (id_page) references webpages (id)
                    on update cascade on delete cascade,
                constraint fk_id_tag foreign key (id_tag) references tags (id)
                    on update cascade on delete cascade
                );
                CREATE TABLE "html_contents"(
                    "page_id"	INTEGER NOT NULL UNIQUE,
                    "html"	TEXT NOT NULL,
                    constraint fk_page_id FOREIGN KEY("page_id") REFERENCES "webpages"("id")
                    on update cascade on delete cascade
                    );
                create virtual table if not exists 'webcontents' using FTS5('id_page' unindexed, 'title', 'content');
                """)
    except sql.Error:
        logger.exception('Ошибка создания таблиц в базе данных')
        close_connection(connector)


def delete_indexes(connector: sql.Connection):
    """Удаляет индексы в базе данных"""
    try:
        with connector:
            connector.executescript(
                """
                begin transaction;
                drop index if exists page_title_idx;
                drop index if exists page_tag_idx;
                commit;
                """
            )
    except sql.Error:
        logger.exception('Ошибка удаления индексов')
        connector.rollback()
        close_connection(connector)


def create_indexes(connector: sql.Connection):
    """Создает индексы в базе данных"""
    try:
        with connector:
            connector.executescript(
                """
                begin transaction;
                create index if not exists page_title_idx on webpages (title);
                create index if not exists page_tag_idx on webpagetags (id_page, id_tag);
                commit;
                """
            )
    except sql.Connection:
        logger.exception('Ошибка создания индексов')
        connector.rollback()
        close_connection(connector)


def add_article(title: str, url: str,
                time_saved: str, htmlContent: str, textContent: str,
                conn: sql.Connection):
    """Запись html страницы в таблицу webpages

    :param textContent: Текст страницы
    :param htmlContent: html-код страницы
    :param conn: Cursor базы данных
    :param title: Заголовок страницы
    :param url: Урл сохраненной страницы
    :param time_saved: Время сохраниния страницы в формате '%Y-%m-%d %H:%M:%S'
    """
    webpage_id = conn.execute(
        """
        insert into webpages (title, url, time_saved, content) values (?, ?, ?, ?);""",
        [title, url, time_saved, htmlContent]).lastrowid
    conn.execute("""insert into webcontents (id_page, title, content) values (?, ?, ?)""",
                 [webpage_id, title, textContent])
    logger.info(f'Добавлена статья "{title}"')


def add_page_tag(url: str, tag_id, cursor: sql.Cursor):
    """Запись данных в таблицы tags и webbpageTags"""
    try:
        # получает id статьи по ее урлу
        # url передается с сервиса Pocket, поэтому статьи может не быть в базе
        id_page = cursor.execute(
            """select id from webpages where url=?;""", (url,)).fetchone()
        if not id_page:
            return
        cursor.execute('insert into webpagetags (id_page, id_tag) VALUES (? ,?)', [id_page[0], tag_id])
    except sql.IntegrityError:
        logger.warning('{}'.format(traceback.format_exc()))


def add_tag(tag, cur: sql.Cursor):
    """
        Добавление тега в таблицу тегов (tags)
    :param tag:
    :param cur:
    :return:
    """
    try:
        tag_id = cur.execute('select id from tags where tag = ?', [tag]).fetchone()
        if tag_id:
            return tag_id[0]
        cur.execute('insert into tags (tag) values (?)', [tag])
        logger.info(f'Add new tag {tag}')
        return cur.lastrowid
    except sql.IntegrityError:
        logger.warning('{}', format(traceback.format_exc()))


def export_articles(folder, cur: sql.Cursor):
    """Экспорт веб-страниц из базы"""
    import os
    count = 0
    directory = '/home/alexandr/Загрузки/html/export'
    folder = folder or directory
    try:
        for id_page, title in cur.execute("""select id, title from webpages;""").fetchall():
            content = cur.execute(
                """select content from webcontents where id_page=?;""", (id_page,)).fetchone()
            title = re.sub('[/?<>*"|]', '', title[:122])
            title = re.sub('( ){2,}', ' ', title)
            fname = os.path.join(folder, title) + '.html'
            if os.path.exists(fname):
                n, _ = os.path.splitext(fname)
                n = n + '_double'
                fname = n + '.html'
            with open(fname, 'w') as f:
                f.write(content[0])
                count += 1
                logger.info(f'Экспортировано "{fname}"')
    except Exception as e:
        logger.exception('Exception in export_articles')
        raise SqliteError(e)
    finally:
        return count

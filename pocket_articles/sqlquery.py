from jinja2 import Template


class SqlQuery:
    """Содержит шаблоны запросов к базе данных.

    all_html: все статьи в базе;
    not_tagged_html: статьи без тегов;
    html_by_tag: статьи по заданному тегу;
    full_text_search: шаблон для полнотекстового поиска.

    """
    all_html: str = """
        select * from all_html
        order by {{ column }} {{ order }}
        limit ? offset ?;"""

    article_data: str = """
        select url, html, tags
        from page_data
        where id={{ page_id }};"""

    not_tagged_html: str = """
        select * from not_tagged_html
        order by {{ column }} {{ order }}
        limit ? offset ?;"""

    html_by_tag: str = """
        select time_saved, title, id
        from html_by_tag
        where id_tag = {{ tag_id }}
        {% raw %}order by {{ column }} {{ order }}{% endraw %}
        limit ? offset ?;"""

    full_text_search = """
        select time_saved, title, id
        from webpages as p
                 join (select id_page
                       from search_table
                       where {{ column }} match '{{ text }}'
                       order by rank) as s on p.id = s.id_page
        limit ? offset ?;"""

    # Колонки для сортировки
    SortTitle = 'lower(title)'  # сортировка по 'title'
    SortDate = 'time_saved'  # сортировка по 'time_saved'

    # Колонки для полнотекстового поиска
    SearchTitle = 'title'
    SearchContent = 'content'

    # Порядок сортировки
    Asc = 'asc'  # сортировка по-возрастанию
    Desc = 'desc'  # сортировка по-убыванию

    @staticmethod
    def get_sql_query(template: str, column: str, order: str) -> str:
        """Сгенерировать запрос к базе

        Получаем запрос к базе в зависимости от выбранной сортировки и
        колонки для сортировки.

        Args:
            template (str): шаблон запроса
            column (str): колонка для сортировки
            order (str): порядок сортировки результатов выборки в базе
        """
        tmpl = Template(template, trim_blocks=True, lstrip_blocks=True)
        return tmpl.render(column=column, order=order)

    @staticmethod
    def get_template_query_by_tag(tagId):
        """Создать шаблон запроса статей по данному тегу

        Args:
            tagId: ID тега
        """
        tpl = Template(SqlQuery.html_by_tag)
        return tpl.render(tag_id=tagId)

    @staticmethod
    def get_query_page_data(pageId):
        """Создать запрос к базе данных для получения данных статьи по ее ID

        Args:
            pageId: ID статьи
        """
        tpl = Template(SqlQuery.article_data, trim_blocks=True, lstrip_blocks=True)
        return tpl.render(page_id=pageId)

    @staticmethod
    def get_full_text_search_query(column: str, text: str):
        """Создать запрос для full-text поиска"""
        tpl = Template(SqlQuery.full_text_search)
        return tpl.render(column=column, text=text)


if __name__ == '__main__':
    import sqlite3
    from pprint import pprint

    print = pprint

    con = sqlite3.connect('/home/alexandr/tmp/pocket/test.db')
    con.enable_load_extension(True)
    con.load_extension('libSqliteIcu')
    t = SqlQuery.get_sql_query(SqlQuery.not_tagged_html, SqlQuery.SortTitle, SqlQuery.Asc)
    data = con.execute(t, [1000, 0]).fetchall()
    print(t)
    print(data)
    con.close()

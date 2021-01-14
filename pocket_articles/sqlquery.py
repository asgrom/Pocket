from dataclasses import dataclass

from jinja2 import Template


@dataclass(eq=False)
class SqlQuery:
    """Содержит шаблоны запросов к базе данных.


    all_html: все статьи в базе;

    not_tagged_html: статьи без тегов;

    html_by_tag: статьи по заданному тегу.
    """
    all_html: str = """
        select * from all_html
        order by {{ column }} {{ order }}
        limit ? offset ?;"""

    article_data: str = "select * from page_data where id={{ pageId }};"

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

    # Колонки для сортировки
    SortTitle = 'lower(title)'  # сортировка по 'title'
    SortDate = 'time_saved'  # сортировка по 'time_saved'

    # Порядок сортировки
    Asc = 'asc'  # сортировка по-возрастанию
    Desc = 'desc'  # сортировка по-убыванию

    @staticmethod
    def get_sql_query(template: str, column: str, order: str) -> str:
        """Получить запрос к базе

        Получаем запрос к базе в зависимости от выбранной сортировки (order)
        и от аргумента query

        Args:
            template (str): что нужно получить в базе - все статьи, статьи по
                тегу или статьи без тегов
            column (str): колонка для сортировки
            order (int): порядок сортировки результатов выборки в базе
        """
        tmpl = Template(template, trim_blocks=True, lstrip_blocks=True)
        return tmpl.render(column=column, order=order)

    @staticmethod
    def get_template_query_by_tag(tagId):
        """Создать шаблон запроса статей по данному тегу"""
        tpl = Template(SqlQuery.html_by_tag)
        return tpl.render(tag_id=tagId)


if __name__ == '__main__':
    import sqlite3
    from pprint import pprint

    print = pprint

    con = sqlite3.connect('/home/alexandr/tmp/pocket/test.db')
    con.enable_load_extension(True)
    con.load_extension('libSqliteIcu')
    tpl = SqlQuery.get_template_query_by_tag(34)
    query = SqlQuery.get_sql_query(tpl, SqlQuery.SortTitle, SqlQuery.Desc)
    # data = con.execute(query, [100, 0]).fetchall()
    # print(data)
    print(tpl)
    print(query)
    con.close()

from dataclasses import dataclass


@dataclass(eq=False)
class SqlQuery:
    """Содержит запросы к базе данных."""
    AllHtml: str = "select * from all_html"
    TitleAsc: str = "select * from html_by_title_asc limit ? offset ?;"
    TitleDesc: str = "select * from html_by_title_desc limit ? offset ?;"
    TimeAsc: str = "select * from html_by_time_asc limit ? offset ?;"
    TimeDesc: str = "select * from html_by_time_desc limit ? offset?;"
    PageData: str = "select * from page_data where id=?;"
    NoTagged: str = "select * from notagged_html"
    NoTaggedTitleAsc: str = "select * from notagged_html_title_asc limit ? offset ?;"
    NoTaggedTitleDesc: str = "select * from notagged_html_title_desc limit ? offset ?;"
    NoTaggedTimeAsc: str = "select * from notagged_html_time_asc limit ? offset ?;"
    NoTaggedTimeDesc: str = "select * from notagged_html_time_desc limit ? offset?;"
    ByTagTitleAsc: str = "select * from html_by_tag_title_asc where id_tag={0} limit ? offset ?;"
    ByTagTitleDesc: str = "select * from html_by_tag_title_desc where id_tag={0} limit ? offset ?;"
    ByTagTimeAsc: str = "select * from html_by_tag_time_asc where id_tag={0} limit ? offset ?;"
    ByTagTimeDesc: str = "select * from html_by_tag_time_desc where id_tag={0} limit ? offset ?;"
    ByTag: str = "select * from html_by_tag"

    SortTitleAsc = 0
    SortTitleDesc = 1
    SortTimeAsc = 2
    SortTimeDesc = 3

    AllArticles = 'all_articles'
    NoTags = 'notags'

    @staticmethod
    def get_sql_query(query: str, order: int) -> str:
        """Получить запрос к базе

        Получаем запрос к базе в зависимости от выбранной сортировки (order)
        и от аргумента query

        Args:
            query (str): что нужно получить в базе - все статьи, статьи по
             тегу или статьи без тегов
            order (int): порядок сортировки результатов выборки в базе
        """
        if query == SqlQuery.AllArticles:
            if order == SqlQuery.SortTitleAsc:
                return SqlQuery.TitleAsc
            elif order == SqlQuery.SortTitleDesc:
                return SqlQuery.TitleDesc
            elif order == SqlQuery.SortTimeAsc:
                return SqlQuery.TimeAsc
            else:
                return SqlQuery.TimeDesc
        elif query == SqlQuery.NoTags:
            if order == SqlQuery.SortTitleAsc:
                return SqlQuery.NoTaggedTitleAsc
            elif order == SqlQuery.SortTitleDesc:
                return SqlQuery.NoTaggedTitleDesc
            elif order == SqlQuery.SortTimeAsc:
                return SqlQuery.NoTaggedTimeAsc
            else:
                return SqlQuery.NoTaggedTimeDesc
        else:
            if order == SqlQuery.SortTitleAsc:
                return SqlQuery.ByTagTitleAsc.format(query)
            elif order == SqlQuery.SortTitleDesc:
                return SqlQuery.ByTagTitleDesc.format(query)
            elif order == SqlQuery.SortTimeAsc:
                return SqlQuery.ByTagTimeAsc.format(query)
            else:
                return SqlQuery.ByTagTimeDesc.format(query)


# Query = namedtuple('Query', [
#     'TitleAsc', 'TitleDesc',
#     'TimeAsc', 'TimeDesc',
#     'PageData',
#     'NoTaggedTitleAsc', 'NoTaggedTitleDesc',
#     'NoTaggedTimeAsc', 'NoTaggedTimeDesc',
#     'ByTagTitleAsc', 'ByTagTitleDesc',
#     'ByTagTimeAsc', 'ByTagTimeDesc'])
#
# SqlQuery = Query(
#     TitleAsc="select * from html_by_title_asc limit ? offset ?;",
#     TitleDesc="select * from html_by_title_desc limit ? offset ?;",
#     TimeAsc="select * from html_by_time_asc limit ? offset ?;",
#     TimeDesc="select * from html_by_time_desc limit ? offset?;",
#     PageData="select * from page_data where id=?;",
#     NoTaggedTitleAsc="select * from notagged_html_title_asc limit ? offset ?;",
#     NoTaggedTitleDesc="select * from notagged_html_title_desc limit ? offset ?;",
#     NoTaggedTimeAsc="select * from notagged_html_time_asc limit ? offset ?;",
#     NoTaggedTimeDesc="select * from notagged_html_time_desc limit ? offset?;",
#     ByTagTitleAsc="select * from html_by_tag_title_asc where id_tag=? limit ? offset ?;",
#     ByTagTitleDesc="select * from html_by_tag_title_desc where id_tag=? limit ? offset ?;",
#     ByTagTimeAsc="select * from html_by_tag_time_asc where id_tag=? limit ? offset ?;",
#     ByTagTimeDesc="select * from html_by_tag_time_desc where id_tag? limit ? offset ?;"
# )


if __name__ == '__main__':
    print(SqlQuery().get_sql_query('all_articles', 0))

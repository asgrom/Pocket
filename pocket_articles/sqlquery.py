from dataclasses import dataclass


@dataclass(eq=False)
class SqlQuery:
    """Содержит запросы к базе данных."""
    TitleAsc: str = "select * from html_by_title_asc limit ? offset ?;"
    TitleDesc: str = "select * from html_by_title_desc limit ? offset ?;"
    TimeAsc: str = "select * from html_by_time_asc limit ? offset ?;"
    TimeDesc: str = "select * from html_by_time_desc limit ? offset?;"
    PageData: str = "select * from page_data where id=?;"
    NoTaggedTitleAsc: str = "select * from notagged_html_title_asc limit ? offset ?;"
    NoTaggedTitleDesc: str = "select * from notagged_html_title_desc limit ? offset ?;"
    NoTaggedTimeAsc: str = "select * from notagged_html_time_asc limit ? offset ?;"
    NoTaggedTimeDesc: str = "select * from notagged_html_time_desc limit ? offset?;"
    ByTagTitleAsc: str = "select * from html_by_tag_title_asc where id_tag=? limit ? offset ?;"
    ByTagTitleDesc: str = "select * from html_by_tag_title_desc where id_tag=? limit ? offset ?;"
    ByTagTimeAsc: str = "select * from html_by_tag_time_asc where id_tag=? limit ? offset ?;"
    ByTagTimeDesc: str = "select * from html_by_tag_time_desc where id_tag? limit ? offset ?;"


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
    print(SqlQuery())

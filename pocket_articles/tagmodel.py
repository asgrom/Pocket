"""Модель для обозревателя тегов."""
import sqlite3

from PyQt5.QtCore import *
from PyQt5.QtGui import *

ID = Qt.UserRole
COUNT = Qt.UserRole + 1


class TagModel(QStandardItemModel):
    notags_req = """
        select count(id) from webpages
        where id not in
        (select id_page from webpagetags);"""

    def __init__(self, con: sqlite3.Connection):
        super(TagModel, self).__init__(parent=None)
        self.con = con
        self.completeModel()

    @pyqtSlot(sqlite3.Connection)
    def setDatabaseConnector(self, con: sqlite3.Connection):
        self.con = con
        self.completeModel()

    def create_all_articles_item(self):
        """Создает QStandardItem все статьи."""
        article_count = self.con.execute(
            """
            select count(id) from webpages;
            """).fetchone()[0]
        all_articles = QStandardItem('Все статьи')
        all_articles.setData('all_articles', ID)
        all_articles.setData(article_count, COUNT)
        all_articles.setIcon(QIcon(QPixmap(':/images/catalog.png')))
        all_articles.setEditable(False)
        return all_articles

    def create_favorites_item(self):
        """Создает QStandardItem с избранным."""
        favorites = QStandardItem('Избранное')
        favorites_id = self.con.execute('select id from tags where tag="Избранное"').fetchone()
        if not favorites_id:
            favorites_id = self.con.execute('insert into tags (tag) values ("Избранное")').lastrowid
            self.con.commit()
        else:
            favorites_id = favorites_id[0]
        favorites.setData(favorites_id, ID)
        favorites.setData(0, COUNT)
        favorites.setIcon(QIcon(QPixmap(':/images/rating.png')))
        favorites.setEditable(False)
        return favorites

    def create_line_item(self):
        """Создает QStandardItem с изображением линии."""
        line = QStandardItem()
        line.setData('line', ID)
        line.setFlags(Qt.NoItemFlags)
        return line

    def create_notags_item(self):
        """Создает QStandardItem без тегов."""
        notags_count = self.con.execute(self.notags_req).fetchone()[0]
        notags = QStandardItem('Без тегов')
        notags.setData('notags', ID)
        notags.setData(notags_count, COUNT)
        notags.setIcon(QIcon(QPixmap(':/images/view.png')))
        notags.setEditable(False)
        return notags

    def create_tags_item(self, favorites_id):
        """Создает QStandardItem с тегами."""
        tags = QStandardItem('Теги')
        tags.setFlags(Qt.NoItemFlags)
        tags.setIcon(QIcon(QPixmap(':/images/tags.png')))
        tags.setData('tags', ID)
        for tag, id_ in self.con.execute('select tag, id from tags;'):
            if id_ == favorites_id:
                continue
            item = QStandardItem('{0}'.format(tag))
            item.setData(0, COUNT)
            item.setData(id_, ID)
            tags.appendRow(item)
        return tags

    @pyqtSlot()
    def completeModel(self):
        """Создание списка тегов статей"""
        self.clear()
        line = self.create_line_item()
        favorites = self.create_favorites_item()
        tags = self.create_tags_item(favorites.data(ID))
        notags = self.create_notags_item()
        all_articles = self.create_all_articles_item()

        self.appendRow(all_articles)
        self.appendRow(line)
        self.appendRow(notags)
        self.appendRow(QStandardItem(line))
        self.appendRow(favorites)
        self.appendRow(QStandardItem(line))
        self.appendRow(tags)
        for count, _id in self.con.execute("""
                select count(tags.id), tags.id
                from tags join webpageTags on tags.id = webpageTags.id_tag
                group by tags.id;"""):
            tag_idx = self.match(self.index(0, 0), ID, _id, 1,
                                 Qt.MatchExactly | Qt.MatchRecursive)[0]
            if tag_idx.data(COUNT) != count:
                self.setData(tag_idx, count, COUNT)

    @pyqtSlot()
    def updateModel(self):
        """Обновление данных в модели отображения тегов статей"""
        #########################################################
        # item "все статьи"
        #########################################################
        all_articles_count = self.con.execute(
            'select count(id) from webpages;').fetchone()[0]

        all_articles_item_idx = self.match(
            self.index(0, 0), ID,
            'all_articles', 1, Qt.MatchExactly)[0]

        if all_articles_item_idx.data(COUNT) != all_articles_count:
            self.setData(
                all_articles_item_idx, all_articles_count, COUNT
            )
        #########################################################
        # item "без тегов"
        #########################################################
        notags_count = self.con.execute(self.notags_req).fetchone()[0]

        notags_idx = self.match(
            self.index(0, 0), ID,
            'notags', 1, Qt.MatchExactly)[0]

        if notags_idx.data(COUNT) != notags_count:
            self.setData(notags_idx, notags_count, COUNT)
        #########################################################
        # item "избранное"
        #########################################################
        favorites_count = self.con.execute(
            """
            select count(id_page) from webpagetags
            where id_tag =
            (select id from tags where tag="Избранное");
            """).fetchone()[0]

        favorites_idx = self.match(
            self.index(0, 0), Qt.DisplayRole,
            'Избранное', 1, Qt.MatchExactly)[0]

        if favorites_idx.data(COUNT) != favorites_count:
            self.setData(favorites_idx, favorites_count, COUNT)
        #########################################################
        # item "теги"
        #########################################################
        tags_item_idx = self.match(
            self.index(0, 0), ID,
            'tags', 1, Qt.MatchExactly)[0]

        for tag, id_ in self.con.execute('select tag, id from tags'):
            tag_item_idx = self.match(
                self.index(0, 0), ID,
                id_, 1, Qt.MatchExactly | Qt.MatchRecursive)

            count = self.con.execute(
                """select count(id_page) from webpagetags where id_tag=?;""",
                [id_]).fetchone()[0]

            if not tag_item_idx:
                item = QStandardItem(tag)
                item.setData(id_, ID)
                item.setData(count, COUNT)
                self.itemFromIndex(tags_item_idx).appendRow([item])
            elif tag_item_idx[0].data(COUNT) != count:
                self.setData(tag_item_idx[0], count, COUNT)

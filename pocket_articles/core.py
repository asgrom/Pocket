# todo:
#   ДОБАВИТЬ ВОЗМОЖНОСТЬ РЕДАКТИРОВАНИЯ НАЗВАНИЯ СТАТЕЙ.
#   сделать что-то с выбором тегов в браузере тегов(чтобы выбирались только актуальные теги)
#   переделать resetCurrentState
#   приделать тулбар
#
#   1.1 ДОбАВИТЬ ВОЗМОЖНОСТЬ ОТКРЫТИЯ HTML В ОТДЕЛЬНОМ ОКНЕ.
#   2. СДЕЛАТЬ ВОЗМОЖНОСТЬ ПЕРЕИМЕНОВАНИЯ ТЕГОВ В ДЕРЕВЕ ТЕГОВ.
#   3. Сделать возможность импорта html по-выбору.
#   4. Сделать возможность загрузки.
#   5. Сделать импорт тегов, статей тегов
#   6. Пересмотреть вызовы логгера
#   7. Проверить все методы с записью в базу на rollback.
#   8. ВОЗМОЖНО ВЫНЕСТИ ВСЕ SQL-ЗАПРОСЫ В МОДУЛЬ РАБОТЫ С БАЗОЙ.
#       МОЖЕТ БЫТЬ СДЕЛАТЬ VIEW В БАЗЕ ДАННЫХ?

import hashlib
import json
import os
import re
import sqlite3 as sql
import sys
import tempfile
import traceback
from datetime import datetime as dt

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtWidgets import *

from . import applogger
from . import dbmethods
from .articletag import ArticleTag, DeleteArticleTagEvent
from .dbmethods import (add_article, connect, export_articles)
from .getpagedata import get_data_from_page, get_page_text_content
from .mainwindow import MainWindow
from .proxystyle import ProxyStyle

logger = applogger.get_logger(__name__)

ID, COUNT = Qt.UserRole, Qt.UserRole + 1


# noinspection PyTypeChecker
def log_uncaught_exceptions(ex_cls, ex, tb):
    text = 'Uncaught exception\n{}: {}:\n'.format(ex_cls.__name__, ex)
    text += ''.join(traceback.format_tb(tb))
    logger.error(text)
    QMessageBox.critical(None, 'Ошибка выполнения', "Возникла ошибка.\nСмотри лог программы.")
    qApp.exit()


sys.excepthook = log_uncaught_exceptions


class Pocket(MainWindow):

    def __init__(self, parent=None):
        super(Pocket, self).__init__(parent)
        self.connect_slots()
        self.load_data_from_db()
        self.loadLastOpenedPage()

    def connect_slots(self):
        """Подключение слотов"""
        self.ui.exportDataBaseAction.triggered.connect(self.export_db_to_html)
        self.ui.actionImportHtml.triggered.connect(self.import_html)
        self.ui.actionNewDB.triggered.connect(self.create_new_db)
        self.ui.actionOpenDbase.triggered.connect(self.open_other_db)
        self.htmlImportedSignal.connect(self.load_data_from_db)
        self.searchPanel.searched.connect(self.search_on_page)

        # контекстное меню дерева тегов
        self.ui.tagsView.customContextMenuRequested.connect(self.tagViewContextMenuRequested)
        self.deleteTagAction.triggered.connect(self.delete_tag_from_tagView)

        # контекстное меню таблицы статей
        self.ui.articleView.customContextMenuRequested['QPoint'].connect(self.articleViewContextMenuRequested)
        self.deleteArticleAction.triggered.connect(self.delete_article)
        self.exportArticleAction.triggered.connect(self.export_article_to_html)

        # меню сортировки статей
        self.ui.actionSortTitleAsc.triggered.connect(
            lambda _, col='title', order='asc': self.articleTitleModel.changeSortOrder(col, order)
        )
        self.ui.actionSortTitleDesc.triggered.connect(
            lambda _, col='title', order='desc': self.articleTitleModel.changeSortOrder(col, order)
        )
        self.ui.actionSortDateAsc.triggered.connect(
            lambda _, col='time_saved', order='asc': self.articleTitleModel.changeSortOrder(col, order)
        )
        self.ui.actionSortDateDesc.triggered.connect(
            lambda _, col='time_saved', order='desc': self.articleTitleModel.changeSortOrder(col, order)
        )

        # выбор статьи для просмотра
        self.ui.articleView.activated.connect(self.open_webpage)

        # выбор в комбобоксе
        # noinspection PyUnresolvedReferences
        self.tagCBox.tagSelected.connect(self.add_new_tag)

        # фильтр заголовков
        self.ui.filterArticleLineEdit.returnPressed.connect(self.set_filter_article_title)
        self.ui.filterArticleLineEdit.returnPressed.connect(self.ui.dbSearch.clear)
        self.ui.filterArticleLineEdit.returnPressed.connect(self.ui.tagFilterLineEdit.clear)

        # выбор по тегу
        self.ui.tagsView.clicked.connect(self.tag_selected)
        self.ui.tagsView.clicked.connect(self.resetCurrentState)

        # поиск по базе
        self.ui.dbSearch.returnPressed.connect(self.db_search)
        self.ui.dbSearch.returnPressed.connect(self.ui.filterArticleLineEdit.clear)
        self.ui.dbSearch.returnPressed.connect(self.ui.tagFilterLineEdit.clear)

        # активируем панель поиска на странице
        QShortcut(QKeySequence.Find, self, self.searchPanel.show)

        self.ui.webView.loadFinished.connect(self.highlight_searched_text)
        self.ui.urlToolButton.toggled.connect(self.show_url_label)
        self.ui.urlToolButton.toggled.connect(self.change_urlToolButton_icon)
        # экспорт таблицы тегов
        self.ui.actionExportTagsTable.triggered.connect(self.export_tags_table)
        # экспорт таблицы webpagetags
        self.ui.actionExportArticleTags.triggered.connect(self.export_article_tags)
        self.ui.actionImportTags.triggered.connect(self.import_tags)
        # фильтр к тегам
        self.ui.tagFilterLineEdit.textChanged.connect(self.tagProxyModel.setFilterRegExp)

    def resetCurrentState(self, idx: QModelIndex):
        """Сбрасываем текущее состояние.

        Удаляем данные о последней открытой статье, строки поиска и фильтра.
        """
        if not idx.isValid() or idx.data(ID) in self.IgnoredTagList or idx.data(ID) is None:
            return
        if self.ui.tagFilterLineEdit.text():
            return
        self._currentOpenedPageID = None
        self._currentOpenedTagID = None
        self._titleFilter = None
        self._searchText = None
        self._tagFilter = None
        self.ui.tagFilterLineEdit.clear()
        self.ui.dbSearch.clear()
        self.ui.filterArticleLineEdit.clear()
        self._currentSortOrder = None
        self.tagCBox.setDisabled(True)

    def loadLastOpenedPage(self):
        """Открываем последнюю активную статью в предыдущем сеансе."""
        if self._currentOpenedPageID is None or self._currentOpenedTagID is None:
            return

        # устанавливаем сортировку, если она была изменена
        if self._currentSortOrder:
            for act in self.sortGroup.actions():
                if act.objectName() == self._currentSortOrder:
                    act.setChecked(True)
                    act.triggered.emit()
                    break

        # устанавливаем фильтр или строку поиска по базе
        if any([self._searchText, self._titleFilter]):
            if self._titleFilter:
                self.ui.filterArticleLineEdit.setText(self._titleFilter)
                self.ui.filterArticleLineEdit.returnPressed.emit()
            elif self._searchText:
                self.ui.dbSearch.setText(self._searchText)
                self.ui.dbSearch.returnPressed.emit()
        else:
            # устанавливаем фильтр в обзоре тегов
            if self._tagFilter:
                self.ui.tagFilterLineEdit.setText(self._tagFilter)
            tagIdx = self.ui.tagsView.model().index(
                self._currentOpenedTagID[0], self._currentOpenedTagID[1],
                self.ui.tagsView.model().index(self._currentOpenedTagID[2], self._currentOpenedTagID[-1])
            )
            self.ui.tagsView.setCurrentIndex(tagIdx)
            self.tag_selected(tagIdx)

        # устанавливаем текущий индекс статьи
        pageIdx = self.ui.articleView.model().index(self._currentOpenedPageID[0], 1)
        if pageIdx.isValid():
            self.ui.articleView.setCurrentIndex(pageIdx)
            self.ui.articleView.scrollTo(pageIdx)
            self.open_webpage(pageIdx)

    @pyqtSlot()
    def import_tags(self):
        # todo:
        #   доделать метод!!!
        file, _ = QFileDialog.getOpenFileName(
            directory=QStandardPaths.writableLocation(QStandardPaths.HomeLocation),
            filter='json (*.json);;All (*)'
        )
        if not file:
            return
        try:
            fh = open(file)
        except OSError:
            logger.exception('Ошибка открытия файла')
            QMessageBox.critical(self, '', 'Ошибка открытия файла. Смотри лог-файл.')
            return
        try:
            self.con.execute('begin transaction;')
            cur = self.con.cursor()
            for data in json.load(fh):
                print(data['tag'])
            QMessageBox.information(self, '', 'Импортирование тегов завершено.')
        except sql.DatabaseError:
            logger.warning(f'Ошибка\n{traceback.format_exc()}')
        except Exception:
            logger.exception('Exception in import tags')
            fh.close()
            cur.close()

    @pyqtSlot()
    def export_article_tags(self):
        """Экспорт таблицы webpagetags."""
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            file, _ = QFileDialog.getSaveFileName(
                directory=os.path.join(
                    QStandardPaths.writableLocation(QStandardPaths.HomeLocation),
                    'articletags.json'),
                filter='json (*.json);;All (*)')
            if not file:
                return
            table_list = dbmethods.export_webpagetags_table(self.con)
            if not table_list:
                QMessageBox.information(self, '', 'У статей нет тегов.')
                return
            if not os.path.splitext(file)[-1]:
                file = file + '.json'
            with open(file, 'w') as fh:
                json.dump(table_list, fh, indent=4, ensure_ascii=False)
            QMessageBox.information(self, '', 'Экспортировано.')
        except sql.DatabaseError:
            logger.exception('Exception in tags table exporting')
            QMessageBox.critical(self, '', 'Ошибка экспорта')
        finally:
            QApplication.restoreOverrideCursor()

    @pyqtSlot()
    def export_tags_table(self):
        """Экспорт таблицы тегов."""
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            tag_list = dbmethods.export_tags_table(self.con)
            if not tag_list:
                QMessageBox.information(self, '', 'Нет тегов.')
                return
            file, _ = QFileDialog.getSaveFileName(
                directory=os.path.join(QStandardPaths.writableLocation(QStandardPaths.HomeLocation), 'tags.json'),
                filter='json (*.json);;All (*)')
            if not file:
                return
            if not os.path.splitext(file)[-1]:
                file = file + '.json'
            with open(file, 'w') as fh:
                json.dump(tag_list, fh, ensure_ascii=False, indent=4)
            QMessageBox.information(self, '', 'Экспортировано.')
        except sql.DatabaseError:
            logger.exception('Exception in webpagetags exporting')
            QMessageBox.critical(self, '', 'Ошибка экспорта')
        finally:
            QApplication.restoreOverrideCursor()

    @pyqtSlot(bool)
    def show_url_label(self, state: bool):
        if not state:
            self.ui.urlLabel.hide()

    @pyqtSlot(bool)
    def change_urlToolButton_icon(self, state: bool):
        if state:
            self.ui.urlToolButton.setIcon(QIcon(':/images/collapse-arrow.png'))
        else:
            self.ui.urlToolButton.setIcon(QIcon(':/images/expand-arrow.png'))

    @pyqtSlot()
    def update_articleTagModel(self):
        """Обновление данных в модели отображения тегов статей"""
        #########################################################
        # item "все статьи"
        #########################################################
        all_articles_count = self.con.execute(
            'select count(id) from webpages;').fetchone()[0]

        all_articles_item_idx = self.articleTagModel.match(
            self.articleTagModel.index(0, 0), ID,
            'all_articles', 1, Qt.MatchExactly)[0]

        if all_articles_item_idx.data(COUNT) != all_articles_count:
            self.articleTagModel.setData(
                all_articles_item_idx, all_articles_count, COUNT
            )
        #########################################################
        # item "без тегов"
        #########################################################
        notags_count = self.con.execute(self.notags_req).fetchone()[0]

        notags_idx = self.articleTagModel.match(
            self.articleTagModel.index(0, 0), ID,
            'notags', 1, Qt.MatchExactly)[0]

        if notags_idx.data(COUNT) != notags_count:
            self.articleTagModel.setData(notags_idx, notags_count, COUNT)
        #########################################################
        # item "избранное"
        #########################################################
        favorites_count = self.con.execute(
            """
            select count(id_page) from webpagetags
            where id_tag =
            (select id from tags where tag="Избранное");
            """).fetchone()[0]

        favorites_idx = self.articleTagModel.match(
            self.articleTagModel.index(0, 0), Qt.DisplayRole,
            'Избранное', 1, Qt.MatchExactly)[0]

        if favorites_idx.data(COUNT) != favorites_count:
            self.articleTagModel.setData(favorites_idx, favorites_count, COUNT)
        #########################################################
        # item "теги"
        #########################################################
        tags_item_idx = self.articleTagModel.match(
            self.articleTagModel.index(0, 0), ID,
            'tags', 1, Qt.MatchExactly)[0]

        for tag, id_ in self.con.execute('select tag, id from tags'):
            tag_item_idx = self.articleTagModel.match(
                self.articleTagModel.index(0, 0), ID,
                id_, 1, Qt.MatchExactly | Qt.MatchRecursive)

            count = self.con.execute(
                """select count(id_page) from webpagetags where id_tag=?;""",
                [id_]).fetchone()[0]

            if not tag_item_idx:
                item = QStandardItem(tag)
                item.setData(id_, ID)
                item.setData(count, COUNT)
                self.articleTagModel.itemFromIndex(tags_item_idx).appendRow([item])
            elif tag_item_idx[0].data(COUNT) != count:
                self.articleTagModel.setData(tag_item_idx[0], count, COUNT)

    @pyqtSlot()
    def delete_tag_from_tagView(self):
        res = QMessageBox.question(self, 'Подтвердить', 'Удалить тег?')
        if res == QMessageBox.No:
            return
        index = self.tagViewSelectionModel.currentIndex()
        if not index.isValid():
            return
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.con.execute('delete from tags where id = ?', [index.data(ID)])
            self.con.commit()
            logger.info(f'Удален тег {index.data(Qt.DisplayRole)}')
            modelIndex = self.tagProxyModel.mapToSource(index)
            self.articleTagModel.removeRow(modelIndex.row(), modelIndex.parent())
            self.tagCBox.completeModel()
        except sql.DatabaseError:
            logger.exception('Ошибка удаления тега')
        else:
            self.update_articleTagModel()
        finally:
            QApplication.restoreOverrideCursor()

    @pyqtSlot()
    def highlight_searched_text(self):
        """Подсветка текста, по которому производили поиск по базе"""
        if self.ui.dbSearch.text() == '':
            return
        text = self.ui.dbSearch.text().replace('"', '').replace('*', '')
        self.ui.webView.findText(text)

    @pyqtSlot(str, QWebEnginePage.FindFlag)
    def search_on_page(self, text, flags):

        def callback(result):
            if not result and text != '':
                self.searchPanel.search_le.setStyleSheet('background: rgba(255, 0, 0, 0.5);')
            else:
                self.searchPanel.search_le.setStyleSheet('background: palette(window);')

        self.ui.webView.findText(text, flags, callback)

    @pyqtSlot()
    def open_other_db(self):
        """Открывает другую базу данных"""
        homedir = QStandardPaths.writableLocation(QStandardPaths.HomeLocation)
        db_path, _ = QFileDialog.getOpenFileName(self, 'Открыть базу данных', homedir,
                                                 "SQLite (*.sqlite *.sqlite3 *.db);;All (*)")
        if not db_path:
            return
        self.con.close()
        self.con = connect(db_path)
        self.database = db_path
        self.articleTitleModel.setCursor(self.con.cursor())
        self.tagCBox.setDatabaseConnector(self.con)
        self.htmlImportedSignal.emit()

    @pyqtSlot()
    def export_article_to_html(self):
        """Экспорт выделенной статьи в HTML"""
        folder = self.get_dir_name()
        if not folder:
            return
        selectedRowsIdx = self.ui.articleView.selectionModel().selectedRows(column=1)
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            for idx in selectedRowsIdx:
                content = self.con.execute(
                    """select html from html_contents where id_page=?""", [idx.data(ID)]
                ).fetchone()[-1]
                fname = re.sub('[/?<>*"|]', '', idx.data(Qt.DisplayRole)[:90])
                fname = re.sub('( ){2,}', ' ', fname) + f'({dt.now()})' + '.html'
                fpath = os.path.join(folder, fname)
                with open(fpath, 'w') as f:
                    f.write(content)
                logger.info(f'Article imported\n"{idx.data(Qt.DisplayRole)}"\n')
        except Exception:
            logger.exception('Error export article')
            QMessageBox.critical(self, 'Ошибка импорта', f'Ошибка импорта статьи', QMessageBox.Ok)
        else:
            QMessageBox.information(self, 'Импортирование завершено', 'Импортирование завершено успешно',
                                    QMessageBox.Ok)
        finally:
            QApplication.restoreOverrideCursor()

    @pyqtSlot()
    def delete_article_tag(self, tag: str):
        """Удаляет тег у статьи в базе"""
        if not self.ui.articleView.currentIndex().isValid():
            return
        cur_index = self.ui.articleView.currentIndex()
        sql_request = """
            delete from webpagetags where id_page=? and 
            id_tag=(select id from tags where tag = ?);
            """
        try:
            self.con.execute(sql_request, [cur_index.data(ID), tag])
            self.con.commit()
            self.update_articleTagModel()
        except sql.Error:
            logger.exception('Exception in delete_article_tag')
            self.con.rollback()
            QMessageBox.warning(self, 'Ошибка', "Ошибка удаления тега статьи")

    def customEvent(self, event):
        if event.type() == DeleteArticleTagEvent.idType:
            self.delete_article_tag(event.tag)

    @pyqtSlot(QPoint)
    def articleViewContextMenuRequested(self, pos: QPoint):
        """Запуск контекстного меню"""
        self.articleViewContextMenu.exec_(self.ui.articleView.mapToGlobal(pos))

    @pyqtSlot(QPoint)
    def tagViewContextMenuRequested(self, pos: QPoint):
        index = self.ui.tagsView.indexAt(pos)
        if not (Qt.ItemIsEditable & index.flags()):
            return
        self.tagViewContextMenu.exec_(self.ui.tagsView.mapToGlobal(pos))

    @pyqtSlot()
    def delete_article(self):
        """Удаляет статью из базы"""
        if self.ui.articleView.selectionModel().selection().isEmpty():
            return
        status = QMessageBox.question(self, 'Подтвердить', 'Удалить статью?',
                                      QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
        if status == QMessageBox.Cancel:
            return
        selectedRowsIdx = self.ui.articleView.selectionModel().selectedRows(column=1)[::-1]
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.con.execute('begin transaction;')
            for idx in selectedRowsIdx:
                self.con.executescript("""
                    delete from webpages where id = {0};
                    delete from search_table where id_page match {0};""".format(idx.data(ID)))
                logger.info(f'Удалена статья "{idx.data(Qt.DisplayRole)}"')
            self.con.commit()

            # вызываем обновление количества статей с тегами.
            self.update_articleTagModel()

            for idx in selectedRowsIdx:
                self.articleTitleModel.removeRow(idx.row())
            QMessageBox.information(self, '', 'Удаление завершено', QMessageBox.Ok)
        except sql.Error:
            self.con.rollback()
            logger.exception('Exception in delete_article')
            QMessageBox.critical(self, 'Ошибка!', 'Ошибка удаления статьи из базы')
        finally:
            QApplication.restoreOverrideCursor()

    @pyqtSlot()
    def db_search(self):
        txt = self.ui.dbSearch.text()
        # устанавливаем текущий курсор на первый индекс тегов.
        self.ui.tagsView.setCurrentIndex(
            self.ui.tagsView.model().index(0, 0)
        )
        QApplication.setOverrideCursor(Qt.WaitCursor)
        if not txt:
            self.articleTitleModel.changeSqlQuery()
        else:
            query = (
                f"""
                select time_saved, webpages.title, id from webpages
                join search_table on id=id_page 
                where search_table.content match '{txt}'
                order by rank limit ? offset ?;""")
            self.articleTitleModel.changeSqlQuery(query)
        QApplication.restoreOverrideCursor()

    @pyqtSlot(QModelIndex)
    def tag_selected(self, index: QModelIndex):
        """Открываем статьи с выбранным тегом в дереве дегов."""
        if not index.isValid() or index.data(ID) in self.IgnoredTagList or index.data(ID) is None:
            return
        tagID = index.data(ID)
        if tagID == 'all_articles':
            self.articleTitleModel.changeSqlQuery()
            return
        if tagID == 'notags':
            query = ("""
                select time_saved, title, id
                from webpages
                where id not in
                (select id_page from webpagetags group by id_page)
                order by lower({}) {} limit ? offset ?;""")
        else:
            query = (
                """select time_saved, title, webpages.id
                from webpages inner join webpagetags w on webpages.id = w.id_page
                where w.id_tag = {0}
                order by lower({{}}) {{}} limit ? offset ?;""".format(tagID))
        self.articleTitleModel.changeSqlQuery(query)

    @pyqtSlot()
    def set_filter_article_title(self):
        """Устанавливает фильтр к статьям"""
        # устанавливаем текущим курсором первый индекс тегов.
        self.ui.tagsView.setCurrentIndex(
            self.ui.tagsView.model().index(0, 0)
        )
        if not self.ui.filterArticleLineEdit.text():
            self.articleTitleModel.changeSqlQuery()
            return
        sql_request = (
            """select time_saved, webpages.title, id
            from webpages join search_table on id=id_page
            where search_table.title match '{0}'
            order by rank limit ? offset ?""".format(
                self.ui.filterArticleLineEdit.text()))
        self.articleTitleModel.changeSqlQuery(sql_request)

    @pyqtSlot(int)
    def add_new_tag(self, index):
        """Добавляет тег из комбобокса к статье

        Если статья уже имеет тег, который задается, то при добавлении в базу присходит исключение - так исключается
        дублирование."""
        insert_article_tag = """insert into webpagetags (id_page, id_tag) VALUES (?, ?)"""
        cur = self.con.cursor()
        cur.execute('begin transaction;')
        try:
            cur.execute(insert_article_tag, [self._currentOpenedPageID[1], self.tagCBox.itemData(index, Qt.UserRole)])
        except sql.DatabaseError:
            self.con.rollback()
            logger.warning('Ошибка установки тега {}\n{}'.format(
                self.tagCBox.itemText(index), traceback.format_exc())
            )
        else:
            self.con.commit()
            self.articleTagsHBox.insertWidget(
                self.articleTagsHBox.count() - 1,
                ArticleTag(self.tagCBox.itemText(index))
            )
            self.update_articleTagModel()
        finally:
            cur.close()

    @pyqtSlot()
    def load_data_from_db(self):
        """Зазрузка заголовков и тегов статей"""
        try:
            self.create_articleTagModel()
            self.ui.tagsView.setCurrentIndex(self.ui.tagsView.model().index(0, 0))
        except Exception:
            logger.exception('Exception in load_data_from_db')

    def create_line_item(self):
        """Создает QStandardItem с изображением линии."""
        line = QStandardItem()
        line.setData('line', ID)
        line.setFlags(Qt.NoItemFlags)
        return line

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

    def create_tags_item(self, favorites_id):
        """Создает QStandardItem с тегами."""
        tags = QStandardItem('Теги')
        tags.setFlags(Qt.NoItemFlags)
        tags.setIcon(QIcon(QPixmap(':/images/tags.png')))
        tags.setData('tags', ID)
        for tag, _id in self.con.execute('select tag, id from tags;'):
            if _id == favorites_id:
                continue
            item = QStandardItem('{0}'.format(tag))
            item.setData(0, COUNT)
            item.setData(_id, ID)
            tags.appendRow(item)
        return tags

    def create_notags_item(self):
        """Создает QStandardItem без тегов."""
        notags_count = self.con.execute(self.notags_req).fetchone()[0]
        # notags_count = 0 if not notags_count else notags_count[0]
        notags = QStandardItem('Без тегов')
        notags.setData('notags', ID)
        notags.setData(notags_count, COUNT)
        notags.setIcon(QIcon(QPixmap(':/images/view.png')))
        notags.setEditable(False)
        return notags

    def create_all_articles_item(self):
        """Создает QStandardItem все статьи."""
        article_count = self.con.execute(
            """
            select count(id) from webpages;
            """).fetchone()[0]
        # article_count = 0 if not article_count else article_count[0]
        all_articles = QStandardItem('Все статьи')
        all_articles.setData('all_articles', ID)
        all_articles.setData(article_count, COUNT)
        all_articles.setIcon(QIcon(QPixmap(':/images/catalog.png')))
        all_articles.setEditable(False)
        return all_articles

    @pyqtSlot()
    def create_articleTagModel(self):
        """Создание списка тегов статей"""
        self.articleTagModel.clear()
        line = self.create_line_item()
        favorites = self.create_favorites_item()
        tags = self.create_tags_item(favorites.data(ID))
        notags = self.create_notags_item()
        all_articles = self.create_all_articles_item()

        self.articleTagModel.appendRow(all_articles)
        self.articleTagModel.appendRow(line)
        self.articleTagModel.appendRow(notags)
        self.articleTagModel.appendRow(QStandardItem(line))
        self.articleTagModel.appendRow(favorites)
        self.articleTagModel.appendRow(QStandardItem(line))
        self.articleTagModel.appendRow(tags)
        for count, _id in self.con.execute("""
                select count(tags.id), tags.id
                from tags join webpageTags on tags.id = webpageTags.id_tag
                group by tags.id;"""):
            tag_idx = self.articleTagModel.match(self.articleTagModel.index(0, 0), ID, _id, 1,
                                                 Qt.MatchExactly | Qt.MatchRecursive)[0]
            if tag_idx.data(COUNT) != count:
                self.articleTagModel.setData(tag_idx, count, COUNT)
        self.ui.tagsView.setExpanded(self.tagProxyModel.mapFromSource(tags.index()), True)

    @pyqtSlot()
    def export_db_to_html(self):
        """Экспорт базы данных в HTML"""
        folder = self.get_dir_name()
        if not folder:
            return
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            count = export_articles(folder, self.con.cursor())
        except Exception:
            logger.exception('Exception in export_db_to_html\n')
            QMessageBox.critical(self, 'Ошибка экспорта', 'Ошибка экспорта\nСмотри лог программы')
        else:
            QMessageBox.information(self, 'Экспортирование завершено', f'Экспортировано {count} статьи',
                                    QMessageBox.Ok)
        finally:
            QApplication.restoreOverrideCursor()

    @pyqtSlot()
    def create_new_db(self):
        """Создание новой базы данных.

        Если у файла базы не задано расширение, то автоматически добавляется расширение (.db).
        """
        dbase_path, _ = QFileDialog.getSaveFileName(
            self, 'Файл базы данных', QStandardPaths.writableLocation(QStandardPaths.HomeLocation),
            "SQLite (*.sqlite *.sql *.sqlite3, *.db);;All files (*)"
        )
        if not dbase_path:
            return
        if not os.path.splitext(dbase_path)[1]:
            dbase_path = os.path.splitext(dbase_path)[0] + '.db'
        self.con.close()
        if os.path.exists(dbase_path):
            os.unlink(dbase_path)
        self.con = connect(dbase_path)
        self.database = dbase_path

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self.ui.statusbar.showMessage('База данных создана')
            logger.info(f'Новая база данных создана {dbase_path}')
            QMessageBox.information(self, 'Готово', 'База данных создана')
            self.import_html()
        except Exception:
            logger.exception('Exception in create new dbase')
            QMessageBox.critical(self, 'Ошибка', 'Ошибка создания базы данных')
        finally:
            self.htmlImportedSignal.emit()
            self.articleTitleModel.setCursor(self.con.cursor())
            QApplication.restoreOverrideCursor()

    @pyqtSlot()
    def import_html(self):
        """Импортирование сохраненных страниц

        Импортирует сохраненные HTML страницы из заданной папки"""
        html_dir = QFileDialog.getExistingDirectory(
            self, 'Каталог HTML страниц',
            QStandardPaths.writableLocation(QStandardPaths.HomeLocation))
        if not html_dir:
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            count = self.write_data_webpages_table(html_dir)
            QMessageBox.information(self, "Имрортирование завершено", f'{count} статей импортировано', QMessageBox.Ok)
            self.ui.statusbar.showMessage(f'{count} статей импортировано в базу данных')
            self.htmlImportedSignal.emit()
        except Exception:
            logger.exception('Exception in import_html')
            QMessageBox.critical(self, 'Ошибка', f'Ошибка импорта страниц')
        finally:
            self.articleTitleModel.resetModel()
            QApplication.restoreOverrideCursor()

    @pyqtSlot()
    def get_dir_name(self):
        try:
            return QFileDialog.getExistingDirectory(
                caption='Выбрать папку',
                directory=QStandardPaths.writableLocation(QStandardPaths.HomeLocation),
                options=QFileDialog.ShowDirsOnly
            )
        except Exception:
            logger.exception('Exception in get_dir_name')
            return

    @pyqtSlot()
    def write_data_webpages_table(self, html_dir):
        """Запись веб-страниц в базу данных"""
        count = 0
        self.con.execute("""begin transaction;""")
        try:
            for file in os.listdir(html_dir):
                if file.endswith('html'):
                    filename = os.path.join(html_dir, file)
                    with open(filename) as f:
                        htmlContent = f.read()
                    hash_ = hashlib.md5(htmlContent.encode()).hexdigest()
                    if self.con.execute('select id from webpages where hash = ?', [hash_]).fetchone() is not None:
                        continue
                    title, url, saved_date = get_data_from_page(filename)
                    textContent = get_page_text_content(htmlContent)
                    try:
                        add_article(title=title, time_saved=saved_date, url=url,
                                    conn=self.con, htmlContent=htmlContent,
                                    textContent=textContent, hash_=hash_)
                        count += 1
                    except sql.IntegrityError:
                        logger.warning("Can't add article\n{}\n{}".format(title, traceback.format_exc()))
        finally:
            self.con.commit()
        return count

    @pyqtSlot(QModelIndex)
    def open_webpage(self, index: QModelIndex):
        """Загрузка статьи"""
        if not index.isValid():
            return
        self.ui.webView.findText('')  # сбрасываем поиск текста на странице
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            url = self.con.execute("""select url from webpages where id=?""",
                                   [index.data(ID)]).fetchone()[0]
            html = self.con.execute("""select html from html_contents where id_page=?""",
                                    [index.data(ID)]).fetchone()[0]
            tags = self.con.execute("""select tag from tags where id in
                                    (select id_tag from webpagetags where id_page = ?);""",
                                    [index.data(ID)]).fetchall()
        except Exception:  # разделить исключения
            logger.exception('Exception in open_webpage')
            QMessageBox.critical(self, 'Ошибка открытия статьи', 'Ошибка открытия страницы')
            QApplication.restoreOverrideCursor()
            return
        # удаляем теги из горизонтального лейаута
        # for i in range(self.articleTagsHBox.count() - 1, -1, -1):
        for i in list(range(self.articleTagsHBox.count()))[::-1]:
            item = self.articleTagsHBox.itemAt(i)
            if isinstance(item.widget(), ArticleTag):
                self.articleTagsHBox.takeAt(i).widget().deleteLater()
        for tag in tags:
            self.articleTagsHBox.insertWidget(
                self.articleTagsHBox.count() - 1, ArticleTag(tag[0]))

        try:
            os.unlink(self._tmphtmlfile)
        except (OSError, TypeError):
            pass

        _, self._tmphtmlfile = tempfile.mkstemp(suffix='.html', text=False)
        with open(self._tmphtmlfile, 'w') as fh:
            fh.write(html)

        self.ui.webView.load(QUrl.fromLocalFile(self._tmphtmlfile))
        self.ui.pageTitleLabel.setText(index.data())
        self.ui.urlLabel.setText(f'<a href="{url}">{url}</a>')
        self.tagCBox.setEnabled(True)

        self._currentOpenedPageID = (index.row(), index.data(ID))
        curTagviewIdx = self.ui.tagsView.currentIndex()
        self._currentOpenedTagID = (
            curTagviewIdx.row(), curTagviewIdx.column(),
            curTagviewIdx.parent().row(), curTagviewIdx.parent().column()
        )
        self._currentSortOrder = self.sortGroup.checkedAction().objectName()
        self._titleFilter = self.ui.filterArticleLineEdit.text()
        self._tagFilter = self.ui.tagFilterLineEdit.text()
        self._searchText = self.ui.dbSearch.text()
        QApplication.restoreOverrideCursor()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.con:
            self.con.close()
        try:
            if self._tmphtmlfile:
                os.unlink(self._tmphtmlfile)
        except OSError:
            logger.exception('Exception in closeEvent unlink self._tmphtmlfile')
        self.save_status()
        event.accept()

    def save_status(self):
        dbpath = os.path.relpath(self.database, os.path.dirname(__file__))
        statusDict = dict(
            dbase=dbpath,
            articleID=self._currentOpenedPageID,
            tagID=self._currentOpenedTagID,
            sortOrder=self._currentSortOrder,
            filter=self._titleFilter,
            search=self._searchText,
            tagFilter=self._tagFilter
        )
        with open(self.configFile, 'w') as fh:
            json.dump(statusDict, fh, ensure_ascii=False, indent=4)


def main():
    sys.argv.append('--disable-web-security')
    app = QApplication(sys.argv)
    app.setStyle(ProxyStyle())

    from qtl18n_ru import localization
    localization.setupRussianLang(app)

    # fh = QFile(':/css/stylesheet.qss')
    fh = QFile('/home/alexandr/PycharmProjects/Pocket/pocket_articles/css/stylesheet.qss')
    if fh.open(QIODevice.ReadOnly | QIODevice.Text):
        app.setStyleSheet(QTextStream(fh).readAll())

    w = Pocket()
    w.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

# todo:
#   ИЗМЕНИТЬ МЕТОД ПОЛУЧЕНИЯ ДАННЫх ИЗ СТРАНИЦЫ, ЧТОбЫ МОжНО бЫЛО
#   ИМПОРТИРОВАТЬ MHTML
#   ДОБАВИТЬ ВОЗМОЖНОСТЬ РЕДАКТИРОВАНИЯ НАЗВАНИЯ СТАТЕЙ.
#   приделать тулбар
#   1.1 ДОбАВИТЬ ВОЗМОЖНОСТЬ ОТКРЫТИЯ HTML В ОТДЕЛЬНОМ ОКНЕ.
#   2. СДЕЛАТЬ ВОЗМОЖНОСТЬ ПЕРЕИМЕНОВАНИЯ ТЕГОВ В ДЕРЕВЕ ТЕГОВ.
#   3. Сделать возможность импорта html по-выбору.
#   4. Сделать возможность загрузки.
#   5. Сделать импорт тегов, статей тегов
#   6. Пересмотреть вызовы логгера
#   7. Проверить все методы с записью в базу на rollback.

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
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import *

from . import applogger
from . import dbmethods
from .articletag import ArticleTag, DeleteArticleTagEvent
from .dbmethods import (add_article, connect, export_articles)
from .getpagedata import get_data_from_page, get_page_text_content
from .mainwindow import MainWindow
from .proxystyle import ProxyStyle
from .sqlquery import SqlQuery

logger = applogger.get_logger(__name__)

ID, COUNT = Qt.UserRole, Qt.UserRole + 1


# noinspection PyTypeChecker
def log_uncaught_exceptions(ex_cls, ex, tb):
    text = 'Uncaught exception\n{}: {}:\n'.format(ex_cls.__name__, ex)
    text += ''.join(traceback.format_tb(tb))
    logger.error(text)
    QMessageBox.critical(None, 'Ошибка выполнения', f"{ex}\nСмотри лог программы.")
    qApp.exit()


sys.excepthook = log_uncaught_exceptions


class Pocket(MainWindow):
    """Класс содержит основные методы графического интерфейса."""
    def __init__(self, parent=None):
        super(Pocket, self).__init__(parent)
        self._currentOpenedPageID = None
        self._tmphtmlfile = None
        self.connect_slots()

    def connect_slots(self):
        """Подключение слотов"""
        self.ui.exportDataBaseAction.triggered.connect(self.export_db_to_html)
        self.ui.actionImportHtml.triggered.connect(self.import_html)
        self.ui.actionNewDB.triggered.connect(self.create_new_db)
        self.ui.actionOpenDbase.triggered.connect(self.open_other_db)
        self.searchPanel.searched.connect(self.search_on_page)

        # обновляем модель обозревателя тегов
        self.tagChanged.connect(self.articleTagModel.updateModel)

        # новое соединение с базой данных
        self.databaseChanged.connect(self.tagCBox.setDatabaseConnector)
        self.databaseChanged.connect(self.articleTagModel.setDatabaseConnector)
        self.databaseChanged.connect(
            lambda x: self.articleTitleModel.setDatabaseConnector(x, self.currentSqlQuery)
        )

        # импортированы новые html
        self.htmlImported.connect(self.articleTitleModel.resetModel)
        self.htmlImported.connect(self.articleTagModel.updateModel)

        # контекстное меню дерева тегов
        self.ui.tagsView.customContextMenuRequested.connect(self.tagViewContextMenuRequested)
        self.deleteTagAction.triggered.connect(self.delete_tag_from_tagView)

        # контекстное меню таблицы статей
        self.ui.articleView.customContextMenuRequested['QPoint'].connect(self.articleViewContextMenuRequested)
        self.deleteArticleAction.triggered.connect(self.delete_article)
        self.exportArticleAction.triggered.connect(self.export_article_to_html)

        # меню сортировки статей
        self.sortGroup.triggered.connect(self.sortMenuTriggered)

        # выбор статьи для просмотра
        self.ui.articleView.activated.connect(self.open_webpage)

        # выбор в комбобоксе
        # noinspection PyUnresolvedReferences
        self.tagCBox.tagSelected.connect(self.add_new_tag)

        # фильтр заголовков
        self.ui.filterArticleLineEdit.returnPressed.connect(self.set_filter_article_title)
        self.ui.filterArticleLineEdit.returnPressed.connect(self.ui.dbSearchLineEdit.clear)
        self.ui.filterArticleLineEdit.returnPressed.connect(self.ui.tagFilterLineEdit.clear)

        # выбор по тегу
        self.ui.tagsView.selectionModel().currentChanged.connect(self.tag_selected)

        # поиск по базе
        self.ui.dbSearchLineEdit.returnPressed.connect(self.search_on_database)
        self.ui.dbSearchLineEdit.returnPressed.connect(self.ui.filterArticleLineEdit.clear)
        self.ui.dbSearchLineEdit.returnPressed.connect(self.ui.tagFilterLineEdit.clear)

        # активируем панель поиска на странице
        QShortcut(QKeySequence.Find, self, self.searchPanel.show)

        # подсветка поискового слова
        self.ui.webView.loadFinished.connect(self.highlight_searched_text)

        # скрытие урла страницы, а также смена иконки кнопки
        self.ui.urlToolButton.toggled.connect(self.show_url_label)
        self.ui.urlToolButton.toggled.connect(self.change_urlToolButton_icon)

        # экспорт таблицы тегов
        self.ui.actionExportTagsTable.triggered.connect(self.export_tags_table)

        # экспорт таблицы webpagetags
        self.ui.actionExportArticleTags.triggered.connect(self.export_article_tags)
        self.ui.actionImportTags.triggered.connect(self.import_tags)

        # фильтр к тегам в обозревателе тегов
        self.ui.tagFilterLineEdit.textChanged.connect(self.setTagFilter)
        self.ui.tagFilterLineEdit.editingFinished.connect(self.ui.filterArticleLineEdit.clear)
        self.ui.tagFilterLineEdit.editingFinished.connect(self.ui.dbSearchLineEdit.clear)

        # удален тег из обозревателя тегов
        self.ui.tagsView.model().rowsRemoved.connect(self.tagCBox.completeModel)

    @pyqtSlot(str)
    def setTagFilter(self, text: str):
        """Устанавливаем фильтр тегов в обозревателе тегов.

        Если текущий индекс в selectionModel валидный, сбрасываем его, чтобы
        при вводе фильтра не было обращений к базе, т.к. будет постоянно
        меняться текущий индекс в модели выбора.
        """
        if self.ui.tagsView.selectionModel().currentIndex().isValid():
            self.ui.tagsView.selectionModel().clearCurrentIndex()
        self.tagProxyModel.setFilterRegExp(text)

    @pyqtSlot(QAction)
    def sortMenuTriggered(self, action):
        """Обработка меню сортировки"""
        if action is self.ui.actionSortTitleAsc or action is self.ui.actionSortTitleDesc:
            self.sortColumn = SqlQuery.SortTitle
        else:
            self.sortColumn = SqlQuery.SortDate
        if action is self.ui.actionSortDateAsc or action is self.ui.actionSortTitleAsc:
            self.sortOrder = SqlQuery.Asc
        else:
            self.sortOrder = SqlQuery.Desc
        query = SqlQuery.get_sql_query(self.currentSqlQuery, self.sortColumn, self.sortOrder)
        self.articleTitleModel.changeSqlQuery(query)

    def testConnection(self):
        print('signal connected main class')
        r = QMessageBox.question(self, '', 'expand?', defaultButton=QMessageBox.Yes)
        if r == QMessageBox.Yes:
            self.ui.tagsView.expandAll()

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
    def delete_tag_from_tagView(self):
        res = QMessageBox.question(self, 'Подтвердить', 'Удалить тег?')
        if res == QMessageBox.No:
            return
        index = self.ui.tagsView.currentIndex()
        if not index.isValid():
            return
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.con.execute('delete from tags where id = ?', [index.data(ID)])
            self.con.commit()
            logger.info(f'Удален тег {index.data(Qt.DisplayRole)}')
            self.ui.tagsView.model().removeRow(index.row(), index.parent())
        except sql.DatabaseError:
            logger.exception('Ошибка удаления тега')
        finally:
            QApplication.restoreOverrideCursor()

    @pyqtSlot()
    def highlight_searched_text(self):
        """Подсветка текста, по которому производили поиск по базе"""
        if self.ui.dbSearchLineEdit.text() == '':
            return
        text = self.ui.dbSearchLineEdit.text().replace('"', '').replace('*', '')
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
        try:
            self.con.close()
            self.con = connect(db_path)
            self.dbFile = db_path
        except Exception:
            logger.exception('Ошибка соединения с базой')
            QMessageBox.critical(self, '', 'Ошибка соединения с базой данных')
            return
        self.currentSqlQuery = SqlQuery.get_sql_query(SqlQuery.all_html, self.sortColumn, self.sortOrder)
        self.databaseChanged.emit(self.con)

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
        # if not self.ui.articleView.currentIndex().isValid():
        #     return
        # cur_index = self.ui.articleView.currentIndex()
        sql_request = """
            delete from webpagetags where id_page=? and 
            id_tag=(select id from tags where tag = ?);
            """
        try:
            self.con.execute(sql_request, [self._currentOpenedPageID, tag])
            self.con.commit()
            self.tagChanged.emit()
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
            self.tagChanged.emit()

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
    def search_on_database(self):
        if not self.ui.dbSearchLineEdit.text():
            return
        self.ui.tagsView.setCurrentIndex(QModelIndex())
        QApplication.setOverrideCursor(Qt.WaitCursor)
        query = SqlQuery.get_full_text_search_query(
            SqlQuery.SearchContent,
            self.ui.dbSearchLineEdit.text()
        )
        self.articleTitleModel.changeSqlQuery(query)
        QApplication.restoreOverrideCursor()

    @pyqtSlot(QModelIndex)
    def tag_selected(self, index: QModelIndex):
        """Открываем статьи с выбранным тегом в дереве тегов."""
        if not index.isValid():
            return
        self.ui.filterArticleLineEdit.clear()
        self.ui.dbSearchLineEdit.clear()
        tagID = index.data(ID)
        if tagID == 'all_articles':
            self.currentSqlQuery = SqlQuery.all_html
        elif tagID == 'notags':
            self.currentSqlQuery = SqlQuery.not_tagged_html
        else:
            tpl = SqlQuery.get_template_query_by_tag(tagID)
            self.currentSqlQuery = tpl
        query = SqlQuery.get_sql_query(self.currentSqlQuery, self.sortColumn, self.sortOrder)
        self.articleTitleModel.changeSqlQuery(query)

    @pyqtSlot()
    def set_filter_article_title(self):
        """Устанавливает фильтр к статьям"""
        if not self.ui.filterArticleLineEdit.text():
            return
        self.ui.tagsView.setCurrentIndex(QModelIndex())
        query = SqlQuery.get_full_text_search_query(
            SqlQuery.SearchTitle,
            self.ui.filterArticleLineEdit.text()
        )
        self.articleTitleModel.changeSqlQuery(query)

    @pyqtSlot(int)
    def add_new_tag(self, index):
        """Добавляет тег из комбобокса к статье

        Если статья уже имеет тег, который задается, то при добавлении в базу присходит исключение - так исключается
        дублирование."""
        insert_article_tag = """insert into webpagetags (id_page, id_tag) VALUES (?, ?)"""
        cur = self.con.cursor()
        cur.execute('begin transaction;')
        try:
            cur.execute(insert_article_tag, [self._currentOpenedPageID, self.tagCBox.itemData(index, ID)])
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
            self.tagChanged.emit()
        finally:
            cur.close()

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
            "SQLite (*.sqlite *.sql *.sqlite3 *.db);;All files (*)"
        )
        if not dbase_path:
            return
        if not os.path.splitext(dbase_path)[1]:
            dbase_path = dbase_path + '.db'
        if os.path.exists(dbase_path):
            os.unlink(dbase_path)

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self.con.close()
            self.con = connect(dbase_path)
            self.dbFile = dbase_path
            self.ui.statusbar.showMessage('База данных создана')
            logger.info(f'Новая база данных создана {dbase_path}')
            QMessageBox.information(self, 'Готово', 'База данных создана')
        except Exception:
            logger.exception('Exception in create new dbase')
            QMessageBox.critical(self, 'Ошибка', 'Ошибка создания базы данных')
        else:
            self.currentSqlQuery = SqlQuery.get_sql_query(SqlQuery.all_html, self.sortColumn, self.sortOrder)
            self.databaseChanged.emit(self.con)
        finally:
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
            count = self.add_html_to_db(html_dir)
            QMessageBox.information(self, "Имрортирование завершено", f'{count} статей импортировано', QMessageBox.Ok)
            self.ui.statusbar.showMessage(f'{count} статей импортировано в базу данных')
            self.htmlImported.emit()
        except Exception:
            logger.exception('Exception in import_html')
            QMessageBox.critical(self, 'Ошибка', f'Ошибка импорта страниц')
        finally:
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
    def add_html_to_db(self, html_dir):
        """Запись веб-страниц в базу данных"""
        count = 0
        self.con.execute("""begin transaction;""")
        try:
            for file in os.listdir(html_dir):
                if os.path.splitext(file)[1] == '.html':
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
            query = SqlQuery.get_query_page_data(index.data(ID))
            url, html, tags = self.con.execute(query).fetchone()
        except Exception:
            logger.exception('Exception in open_webpage')
            QMessageBox.critical(self, 'Ошибка открытия статьи', 'Ошибка открытия страницы')
            QApplication.restoreOverrideCursor()
            return
        # удаляем теги из горизонтального лейаута
        for i in list(range(self.articleTagsHBox.count()))[::-1]:
            item = self.articleTagsHBox.itemAt(i)
            if isinstance(item.widget(), ArticleTag):
                self.articleTagsHBox.takeAt(i).widget().deleteLater()
        if tags:
            for tag in tags.split(','):
                self.articleTagsHBox.insertWidget(
                    self.articleTagsHBox.count() - 1, ArticleTag(tag))

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
        self._currentOpenedPageID = index.data(ID)
        QApplication.restoreOverrideCursor()

    def closeEvent(self, event: QCloseEvent) -> None:
        # self.articleTitleModel.deleteLater()
        if self.con:
            self.con.close()
        try:
            if self._tmphtmlfile:
                os.unlink(self._tmphtmlfile)
        except OSError:
            logger.exception('Exception in closeEvent unlink self._tmphtmlfile')
        QWebEngineProfile.defaultProfile().clearHttpCache()
        self.save_status()
        event.accept()

    def save_status(self):
        dbpath = os.path.abspath(self.dbFile)
        statusDict = dict(dbase=dbpath)
        with open(self.configFile, 'w') as fh:
            json.dump(statusDict, fh, ensure_ascii=False, indent=4)


def main():
    sys.argv.append('--disable-web-security')
    app = QApplication(sys.argv)
    app.setStyle(ProxyStyle())

    from qtl18n_ru import localization
    localization.setupRussianLang(app)

    fh = QFile(':/css/stylesheet.qss')
    # fh = QFile('/home/alexandr/PycharmProjects/Pocket/pocket_articles/css/stylesheet.qss')
    if fh.open(QIODevice.ReadOnly | QIODevice.Text):
        app.setStyleSheet(QTextStream(fh).readAll())

    w = Pocket()
    w.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

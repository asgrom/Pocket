import json
import os

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import QWebEngineSettings
from PyQt5.QtWidgets import *

from .dbmethods import connect
from .delegate import Delegate
from .mainui import Ui_MainUI
from .searchpanel import SearchPanel
from .tablemodel import TableModel
from .tagcombobox import TagsComboBox
from .treeviewproxymodel import TreeViewProxyModel


class MainWindow(QMainWindow):
    htmlImportedSignal = pyqtSignal()

    notags_req = """
        select count(id) from webpages
        where id not in
        (select id_page from webpagetags);"""

    database = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data/articles.db')
    configFile = os.path.join(os.path.dirname(__file__), 'config/config.json')
    ignoredTags = ['line', 'tags']

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        # временный HTML файл
        self._tmphtmlfile = None
        # текущая открытая статья ID
        self._currentOpenedPageID = None
        self._currentOpenedTagID = None
        self._currentSortOrder = None
        self._filterText = None
        self._searchText = None

        self.config_parser()
        # создание соединения с базой данных
        self.con = connect(self.database)

        settings = QWebEngineSettings.defaultSettings()
        settings.setAttribute(QWebEngineSettings.AllowRunningInsecureContent, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)

        self.ui = Ui_MainUI()
        self.ui.setupUi(self)
        self.loadUi()

    def config_parser(self):
        if os.path.exists(self.configFile):
            with open(self.configFile) as fh:
                statusDict = json.load(fh)
            if statusDict.get('dbase') is not None:
                self.database = os.path.abspath(
                    os.path.join(
                        os.path.dirname(__file__),
                        statusDict.get('dbase'))
                )
            self._currentSortOrder = statusDict.get('sortOrder')
            self._currentOpenedTagID = statusDict.get('tagID')
            self._currentOpenedPageID = statusDict.get('articleID')
            self._filterText = statusDict.get('filter')
            self._searchText = statusDict.get('search')

    def loadUi(self):
        """Инициализация основных элементов интерфеса"""
        # иконка лупы в строке поиска по базе
        self.ui.dbSearch.addAction(QIcon(':/images/search-50.svg'), QLineEdit.LeadingPosition)
        # иконка в строку фильтра
        self.ui.filterArticleLineEdit.addAction(QIcon(':/images/filter_list.svg'), QLineEdit.LeadingPosition)
        # прячем label с url
        self.ui.urlLabel.hide()

        ################################################################################
        # отображение списка статей
        ################################################################################
        self.articleTitleModel = TableModel(self.con.cursor())
        self.articleTitleModel.setObjectName('ArticleList')
        self.ui.articleView.setSortingEnabled(False)
        self.ui.articleView.verticalHeader().setVisible(True)
        self.ui.articleView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.articleView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.ui.articleView.setModel(self.articleTitleModel)

        ################################################################################
        # отображение списка тегов статей
        ################################################################################
        self.articleTagModel = QStandardItemModel()
        self.ui.tagsView.setItemDelegate(Delegate())
        self.ui.tagsView.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ui.tagsView.setHeaderHidden(True)
        self.ui.tagsView.setSortingEnabled(True)
        self.ui.tagsView.sortByColumn(0, Qt.AscendingOrder)
        self.tagProxyModel = TreeViewProxyModel()
        self.tagProxyModel.setSortCaseSensitivity(Qt.CaseInsensitive)
        # noinspection PyTypeChecker
        self.tagProxyModel.setSourceModel(self.articleTagModel)
        self.ui.tagsView.setModel(self.tagProxyModel)
        self.tagViewSelectionModel = self.ui.tagsView.selectionModel()

        ################################################################################
        # HBoxLayout с комбобоксом со списком тегов и теги выбранной статьи
        ################################################################################
        self.articleTagsHBox = QHBoxLayout()
        self.tagIcon = QLabel()
        self.tagIcon.setPixmap(QPixmap(':/images/tag.png'))
        self.tagIcon.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.tagCBoxModel = QStandardItemModel()
        self.tagCBox = TagsComboBox()
        self.tagCBox.setModel(self.tagCBoxModel)
        self.articleTagsHBox.addWidget(self.tagIcon)
        self.articleTagsHBox.addWidget(self.tagCBox)
        self.articleTagsHBox.addStretch(1)  # пружина в конце бокса
        self.ui.verticalLayout_2.insertLayout(2, self.articleTagsHBox)

        ################################################################################
        # SearchPanel
        ################################################################################
        self.searchPanel = SearchPanel()
        self.searchPanel.hide()
        self.ui.verticalLayout_2.addWidget(self.searchPanel)

        ################################################################################
        # QMenu Контекстное меню для articleTitleView
        ################################################################################
        self.articleViewContextMenu = QMenu()
        self.deleteArticleAction = QAction('Удалить статью')
        self.articleViewContextMenu.addAction(self.deleteArticleAction)
        self.exportArticleAction = QAction('Экспорт в HTML')
        self.articleViewContextMenu.addAction(self.exportArticleAction)
        self.ui.articleView.setContextMenuPolicy(Qt.CustomContextMenu)

        ################################################################################
        # Контекстное меню для articleTagView
        ################################################################################
        self.tagViewContextMenu = QMenu()
        self.deleteTagAction = QAction('Удалить тег')
        self.tagViewContextMenu.addAction(self.deleteTagAction)
        self.ui.tagsView.setContextMenuPolicy(Qt.CustomContextMenu)

        ################################################################################
        # Меню сортировки статей
        ################################################################################
        self.sortGroup = QActionGroup(self.ui.sortArticlesSubmenu)
        self.sortGroup.addAction(self.ui.actionSortDateDesc)
        self.sortGroup.addAction(self.ui.actionSortDateAsc)
        sep = QAction()
        sep.setSeparator(True)
        self.sortGroup.addAction(sep)
        self.sortGroup.addAction(self.ui.actionSortTitleDesc)
        self.sortGroup.addAction(self.ui.actionSortTitleAsc)
        self.sortGroup.setExclusive(True)
        self.ui.sortArticlesSubmenu.addActions(self.sortGroup.actions())

        ################################################################################
        # иконки для меню
        ################################################################################
        self.ui.actionNewDB.setIcon(QIcon(':/images/database-plus.svg'))
        self.ui.actionImportHtml.setIcon(QIcon(':/images/database-import.svg'))
        self.ui.exportDataBaseAction.setIcon(QIcon(':/images/database-export.svg'))
        self.ui.actionExit.setIcon(QIcon(':/images/icons8-exit-50.png'))
        self.ui.actionOpenDbase.setIcon(QIcon(':/images/database.svg'))

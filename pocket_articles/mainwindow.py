import json
import os
import sqlite3

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import *

from .dbmethods import connect
from .delegate import Delegate
from .dialog import Dialog
from .mainui import Ui_MainUI
from .searchpanel import SearchPanel
from .sqlquery import SqlQuery
from .articlemodel import ArticleModel
from .tagcombobox import TagsComboBox
from .tagmodel import TagModel
from .treeviewproxymodel import TreeViewProxyModel


class MainWindow(QMainWindow):
    htmlImported = pyqtSignal()
    tagChanged = pyqtSignal()
    databaseChanged = pyqtSignal(sqlite3.Connection)

    dbFile = None
    configFile = os.path.join(os.path.dirname(__file__), 'config/config.json')

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.sortOrder = SqlQuery.Desc
        self.currentSqlQuery = SqlQuery.all_html
        self.sortColumn = SqlQuery.SortDate

        settings = QWebEngineSettings.defaultSettings()
        settings.setAttribute(QWebEngineSettings.AllowRunningInsecureContent, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        profile = QWebEngineProfile.defaultProfile()
        profile.setHttpCacheType(QWebEngineProfile.NoCache)

        self.ui = Ui_MainUI()
        self.ui.setupUi(self)

        self.config_parser()
        if not MainWindow.dbFile:
            dbFile = Dialog.getDatabaseFile(self)
            if not dbFile:
                raise Exception('No Database File')
            MainWindow.dbFile = dbFile

        self.con = connect(self.dbFile)

        self.initUI()

    def config_parser(self):
        if os.path.exists(self.configFile):
            with open(self.configFile) as fh:
                statusDict = json.load(fh)
            if statusDict.get('dbase') is not None:
                MainWindow.dbFile = os.path.abspath(statusDict.get('dbase'))

    def initUI(self):
        """Инициализация основных элементов интерфеса"""
        # иконка лупы в строке поиска по базе
        self.ui.dbSearchLineEdit.addAction(QIcon(':/images/search-50.svg'), QLineEdit.LeadingPosition)
        # иконка в строку фильтра
        self.ui.filterArticleLineEdit.addAction(
            QIcon(':/images/filter_list.svg'),
            QLineEdit.LeadingPosition
        )
        self.ui.tagFilterLineEdit.addAction(
            QIcon(':/images/filter_list.svg'),
            QLineEdit.LeadingPosition
        )
        # прячем label с url
        self.ui.urlLabel.hide()
        # self.ui.articleViewFrame.setContentsMargins(0, 0, 0, 0)
        self.ui.articleViewFrameLayout.setContentsMargins(5, 5, 5, 0)
        self.changePalette()

        ################################################################################
        # отображение списка статей
        ################################################################################
        query = SqlQuery.get_sql_query(self.currentSqlQuery, self.sortColumn, self.sortOrder)
        self.articleTitleModel = ArticleModel(self.con, query)
        self.articleTitleModel.setObjectName('ArticleList')
        self.ui.articleView.setSortingEnabled(False)
        self.ui.articleView.verticalHeader().setVisible(True)
        # режим выбора. здесь выбор построчно
        self.ui.articleView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.articleView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.ui.articleView.setModel(self.articleTitleModel)

        ################################################################################
        # отображение списка тегов статей
        ################################################################################
        self.articleTagModel = TagModel(self.con)
        self.ui.tagsView.setItemDelegate(Delegate())
        self.ui.tagsView.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ui.tagsView.setHeaderHidden(True)
        self.ui.tagsView.setSortingEnabled(True)
        self.ui.tagsView.sortByColumn(0, Qt.AscendingOrder)
        self.tagProxyModel = TreeViewProxyModel()
        # noinspection PyTypeChecker
        self.tagProxyModel.setSourceModel(self.articleTagModel)
        self.ui.tagsView.setModel(self.tagProxyModel)
        self.ui.tagsView.expandAll()

        ################################################################################
        # HBoxLayout с комбобоксом со списком тегов и теги выбранной статьи
        ################################################################################
        self.articleTagsHBox = QHBoxLayout()
        self.tagIcon = QLabel()
        self.tagIcon.setPixmap(QPixmap(':/images/tag.png'))
        self.tagIcon.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.tagCBox = TagsComboBox(self.con)
        self.tagCBox.setDisabled(True)
        self.articleTagsHBox.addWidget(self.tagIcon)
        self.articleTagsHBox.addWidget(self.tagCBox)
        self.articleTagsHBox.addStretch(1)  # пружина в конце бокса
        self.ui.articleViewFrameLayout.insertLayout(2, self.articleTagsHBox)
        self.ui.pageTitleLineEdit.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.ui.pageTitleLineEdit.setPlaceholderText('Название статьи')

        ################################################################################
        # SearchPanel
        ################################################################################
        self.searchPanel = SearchPanel()
        self.searchPanel.hide()
        self.ui.articleViewFrameLayout.addWidget(self.searchPanel)

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

    def changePalette(self):
        """Устанавливаем цвета для текста, подсветки текста и самого
         подсвеченного текста."""
        palette = qApp.palette()
        # текст
        palette.setColor(QPalette.Text, QColor(63, 63, 63))
        # подсветка
        # palette.setColor(QPalette.Highlight, QColor(210, 210, 210, 255))
        # подсвеченный текст
        # palette.setColor(QPalette.HighlightedText, QColor(49, 117, 168, 255))
        # palette.setColor(QPalette.HighlightedText, Qt.blue)
        qApp.setPalette(palette)

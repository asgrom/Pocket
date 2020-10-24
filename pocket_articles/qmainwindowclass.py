from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QStandardItemModel, QPixmap, QIcon, QKeySequence
from PyQt5.QtWebEngineWidgets import QWebEngineSettings
from PyQt5.QtWidgets import (QMainWindow, QHeaderView, QHBoxLayout, QLabel, QSizePolicy, QMenu, QActionGroup,
                             QAction, QShortcut, QLineEdit)

from .changedb import connect
from .mainui import Ui_MainUI
from .qdelegate import Delegate
from .qsearchpanel import SearchPanel
from .qtablemodel import TableModel
from .qtagcombobox import TagsComboBox
from .qtreeproxymodel import TreeViewProxyModel


class MainWindow(QMainWindow):
    htmlImportedSignal = pyqtSignal()
    notags_req = """select count(id) from webpages
            where id not in
            (select id_page from webpagetags);"""

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.delegate = Delegate()
        # создание соединения с базой данных
        self.con = connect()

        # список временных файлов, которые при закрытии будут удалятся
        self._tmphtmlfile = None

        settings = QWebEngineSettings.defaultSettings()
        settings.setAttribute(QWebEngineSettings.AllowRunningInsecureContent, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)

        self.ui = Ui_MainUI()
        self.ui.setupUi(self)
        self.loadUi()

    def loadUi(self):
        """Инициализация основных элементов интерфеса"""
        # иконка лупы в строке поиска по базе
        self.ui.dbSearch.addAction(QIcon(':/images/search-50.svg'), QLineEdit.LeadingPosition)
        # иконка в строку фильтра
        self.ui.filterArticleLineEdit.addAction(QIcon(':/images/filter_list.svg'), QLineEdit.LeadingPosition)

        ################################################################################
        # отображение списка статей
        ################################################################################
        self.articleTitleModel = TableModel(self.con.cursor())
        self.articleTitleModel.setObjectName('ArticleList')
        self.ui.articleView.setSortingEnabled(False)
        self.ui.articleView.verticalHeader().setVisible(True)
        self.ui.articleView.setModel(self.articleTitleModel)

        ################################################################################
        # отображение списка тегов статей
        ################################################################################
        self.articleTagModel = QStandardItemModel()
        self.ui.tagsView.setItemDelegate(self.delegate)
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
        self.ui.verticalLayout_2.insertLayout(1, self.articleTagsHBox)

        ################################################################################
        # SearchPanel
        ################################################################################
        self.searchPanel = SearchPanel()
        self.searchPanel.hide()
        self.ui.verticalLayout_2.addWidget(self.searchPanel)
        self.searchPanel.searched.connect(self.search_on_page)

        ################################################################################
        # QMenu Контекстное меню для articleTitleView
        ################################################################################
        self.articleViewContextMenu = QMenu()
        self.articleViewContextMenu.addAction('Удалить статью', self.delete_article)
        self.articleViewContextMenu.addAction('Экспортировать статью в HTML', self.export_article_to_html)
        self.ui.articleView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.articleView.customContextMenuRequested['QPoint'].connect(self.articleViewContextMenuRequested)

        ################################################################################
        # Контекстное меню для articleTagView
        ################################################################################
        self.tagViewContextMenu = QMenu()
        self.tagViewContextMenu.addAction('Удалить тег', self.delete_tag_from_tagView)
        self.ui.tagsView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.tagsView.customContextMenuRequested.connect(self.tagViewContextMenuRequested)

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

        ################################################################################
        # иконки для меню
        ################################################################################
        self.ui.actionNewDB.setIcon(QIcon(':/images/database-plus.svg'))
        self.ui.actionNewDBPocket.setIcon(QIcon(':/images/database-plus.svg'))
        self.ui.actionImportHtml.setIcon(QIcon(':/images/database-import.svg'))
        self.ui.exportDataBaseAction.setIcon(QIcon(':/images/database-export.svg'))
        self.ui.actionExit.setIcon(QIcon(':/images/icons8-exit-50.png'))
        self.ui.actionOpenDbase.setIcon(QIcon(':/images/database.svg'))

        ################################################################################
        # Соединение сигналов
        ################################################################################
        self.ui.exportDataBaseAction.triggered.connect(self.export_db_to_html)
        self.ui.actionImportHtml.triggered.connect(self.import_html)
        self.ui.actionNewDBPocket.triggered.connect(self.create_new_db)
        self.ui.actionNewDB.triggered.connect(self.create_new_db)
        self.ui.actionOpenDbase.triggered.connect(self.open_other_db)
        self.htmlImportedSignal.connect(self.load_data_from_db)
        # выбор статьи для просмотра
        self.ui.articleView.selectionModel().selectionChanged.connect(self.open_webpage)
        # выбор в комбобоксе
        # noinspection PyUnresolvedReferences
        self.tagCBox.activated.connect(self.add_new_tag)
        # фильтр в прокси-модели
        self.ui.filterArticleLineEdit.returnPressed.connect(self.set_filter_article_title)
        self.ui.filterArticleLineEdit.returnPressed.connect(self.ui.dbSearch.clear)
        # выбор по тегу
        self.tagViewSelectionModel.selectionChanged.connect(self.tag_selected)
        # поиск по базе
        self.ui.dbSearch.returnPressed.connect(self.db_search)
        self.ui.dbSearch.returnPressed.connect(self.ui.filterArticleLineEdit.clear)
        QShortcut(QKeySequence.Find, self, self.searchPanel.show)
        # будут перехватываться события для фрейма, к которому принадлежит ArticleTag
        # в частности, событие удаление тега у статьи
        self.ui.articleViewFrame.customEvent = self.customEvent
        self.ui.webView.loadFinished.connect(self.highlight_searched_text)

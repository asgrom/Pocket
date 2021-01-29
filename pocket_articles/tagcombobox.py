import sqlite3

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from . import applogger

logger = applogger.get_logger(__name__)


class TagsComboBox(QComboBox):
    """Комбобокс со списком тегов"""

    defaultText = 'Add tag'
    tagSelected = pyqtSignal(int)

    def __init__(self, con: sqlite3.Connection, parent=None):
        super(TagsComboBox, self).__init__(parent)
        self.con = con

        self.completeModel()
        self.initUI()

        #######################################################################
        # Connect Signals
        #######################################################################
        # noinspection PyUnresolvedReferences
        self.textActivated.connect(self.textActivatedSlot)
        self.lineEdit().textChanged.connect(self.changeWidth)

    def initUI(self):
        """Инициализируем настройки интерфейса."""
        self.setEditable(True)
        self.lineEdit().setPlaceholderText(self.defaultText)
        self.lineEdit().setClearButtonEnabled(True)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.setInsertPolicy(QComboBox.InsertAlphabetically)
        self.lineEdit().setStyleSheet(
            'background: transparent;'
            'border-top-left-radius: 9px;'
            'border-bottom-left-radius: 9px;'
            'padding-left: 5px;'
        )

    @pyqtSlot()
    def completeModel(self):
        """Заполняем модель из базы."""
        self.model().clear()
        for (id_, tag) in self.con.execute('select id, tag from tags order by lower(tag);'):
            item = QStandardItem(tag)
            item.setData(str(id_), Qt.UserRole)
            self.model().appendRow(item)
        self.setCurrentIndex(-1)

    @pyqtSlot(str)
    def textActivatedSlot(self, text):
        """Добавляем новый тег в базу.

        Добавляем ID тега в итем комбобокса. Генерируем сигнал о том,
        что выбран новый пункт комбобокса."""
        tag = text
        id_ = self.currentData(Qt.UserRole)
        if not id_:
            try:
                self.con.execute('begin transaction;')
                id_ = self.con.execute(
                    'insert into tags (tag) values (?);',
                    [tag]
                ).lastrowid
            except sqlite3.Error:
                logger.exception('Error add tag to DB')
                self.con.rollback()
                self.removeItem(self.currentIndex())
                self.setCurrentIndex(-1)
                return
            else:
                self.con.commit()
            self.setItemData(self.currentIndex(), id_, Qt.UserRole)
        self.tagSelected.emit(self.currentIndex())
        self.setCurrentIndex(-1)

    @pyqtSlot(sqlite3.Connection)
    def setDatabaseConnector(self, con: sqlite3.Connection):
        """Устанавливаем соединение с базой данных."""
        self.con = con
        self.completeModel()

    def changeWidth(self, text):
        """Меняем размер комбобокса по мере ввода текста."""
        width = self.lineEdit().fontMetrics().width(text)
        self.setMinimumWidth(width + 55)

    def showPopup(self):
        """расширяет всплывающее окно до ширины элементов"""
        self.view().setMinimumWidth(self.view().sizeHintForColumn(0))
        super().showPopup()

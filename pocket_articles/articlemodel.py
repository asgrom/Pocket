import sqlite3
import typing

from PyQt5.QtCore import *
from PyQt5.QtWidgets import QApplication, QWidget

from . import applogger

logger = applogger.get_logger(__name__)


class ArticleModel(QAbstractTableModel):
    """Модель со статьями"""

    def __init__(self, con: sqlite3.Connection, query: str,
                 numberRows=100, parent: QWidget = None):
        """
        Args:
            con (sqlite3.Connection): Соединение с базой данных.
            query (str):
            numberRows (int): Количество строк, получаемых из базы за один
                запрос, (default 100)
            parent (QWidget):
        """
        super(ArticleModel, self).__init__(parent)
        self.con = con
        self.numberRows = numberRows  # количество строк для считывания из базы
        self.query = query
        self.dbData = []  # данные из базы
        self.horizontalHeaderLabels = ['Дата', 'Название статьи']
        self._columnCount = 2
        self._rowCount = 0
        self._canFetchMore = True

    @pyqtSlot()
    def resetModel(self):
        self.beginResetModel()
        self.dbData.clear()
        self._canFetchMore = True
        self._rowCount = 0
        self.endResetModel()

    @pyqtSlot(sqlite3.Cursor)
    def setDatabaseConnector(self, con: sqlite3.Connection, query: str):
        """Устанавливает соединение с базой данных.

        Устанавливаем новое соединение с базой.

        Args:
            con (sqlite3.Connection):
            query (str):
        """
        self.con = con
        self.query = query
        self.resetModel()

    @pyqtSlot()
    def changeSqlQuery(self, query):
        """Изменение sql-запроса

        Args:
            query (str): Запрос к базе данных.
        """
        self.query = query
        self.resetModel()

    def data(self, index: QModelIndex, role: int = ...) -> typing.Any:
        """Выдем данные статьи

        Колонку с датой преобразовываем из вида YMD в DMY.
        Меняем фон нечетных строк меняем на альтернативный.
        Args:
            index (QModelIndex):
            role (int):
        """
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            if index.column() == 0:
                date = QDateTime.fromString(
                    self.dbData[index.row()][index.column()],
                    'yyyy-MM-dd hh:mm:ss'
                ).toString('dd-MM-yyyy hh:mm:ss')
                return date
            return self.dbData[index.row()][index.column()]
        if role == Qt.UserRole:
            return self.dbData[index.row()][-1]
        if role == Qt.BackgroundRole:
            if (index.row() % 2) == 0:
                return QApplication.palette().base()
            else:
                return QApplication.palette().alternateBase()
        return

    def refreshData(self):
        """Обновляет данные в модели.

        Обновляем данные в модели и подаем сигнал на обновление layout'a
        вьюхи модели.
        """
        self.layoutAboutToBeChanged.emit()
        self.dbData = self.con.execute(self.query, [self._rowCount, 0]).fetchall()
        persistentIndexList = self.persistentIndexList()
        self.changePersistentIndexList(
            persistentIndexList,
            [QModelIndex() for _ in range(len(persistentIndexList))]
        )
        self.layoutChanged.emit()

    def canFetchMore(self, parent: QModelIndex) -> bool:
        """
        Args:
            parent (QModelIndex):
        """
        return self._canFetchMore

    def fetchMore(self, parent: QModelIndex) -> None:
        """Получаем данные из базы.

        Если данные из базы не получены, то выставляем атрибут _canFetchMore
        в False.

        Args:
            parent (QModelIndex):
        """
        try:
            data = self.con.execute(
                self.query,
                [self.numberRows, self._rowCount]).fetchall()
        except sqlite3.Error:
            logger.exception('Exception in fetchMore')
            self._canFetchMore = False
            return

        rows = len(data)

        if rows == 0:
            self._canFetchMore = False
            return

        self.dbData.extend(data)

        self.beginInsertRows(
            QModelIndex(),
            self._rowCount,
            self._rowCount + rows - 1
        )
        self._rowCount += rows
        if rows < self.numberRows:
            self._canFetchMore = False
        else:
            self._canFetchMore = True
        self.endInsertRows()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """
        Args:
            parent (QModelIndex):
        """
        return self._rowCount

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """
        Args:
            parent (QModelIndex):
        """
        return self._columnCount

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> typing.Any:
        """
        Args:
            section (int):
            orientation (Qt.Orientation):
            role (int):
        """
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.horizontalHeaderLabels[section]
        return super(ArticleModel, self).headerData(section, orientation, role)

    def removeRow(self, row: int, parent: QModelIndex = QModelIndex()) -> bool:
        """
        Args:
            row (int):
            parent (QModelIndex):
        """
        self.beginRemoveRows(parent, row, row)
        try:
            status = self.dbData.pop(row)
            self._rowCount -= 1
        except IndexError:
            status = False
        self.endRemoveRows()
        if status:
            return True
        return False

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

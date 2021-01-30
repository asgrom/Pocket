import sqlite3
import typing

from PyQt5.QtCore import *
from PyQt5.QtWidgets import QApplication, QWidget

from . import applogger

logger = applogger.get_logger(__name__)


class ArticleModel(QAbstractTableModel):
    """Модель со статьями"""

    def __init__(self, con: sqlite3.Connection, query: str,
                 number_rows=100, parent: QWidget = None):
        """
        Args:
            con (sqlite3.Connection): Соединение с базой данных.
            query (str):
            number_rows (str): Количество строк, получаемых из базы за один
                запрос, (default 100)
            parent (QWidget):
        """
        super(ArticleModel, self).__init__(parent)
        self.con = con
        self.number_rows = number_rows  # количество строк для считывания из базы
        self.query = query
        self.dbData = []  # данные из базы
        self.chunkData = []  # порция данных из базы
        self.horizontalHeaderLabels = ['Дата', 'Название статьи']
        self._columnCount = 2
        self._offset = 0  # количество полученных строк из базы

    @pyqtSlot()
    def resetModel(self):
        self.beginResetModel()
        self.chunkData.clear()
        self.dbData.clear()
        self._offset = 0
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
                return QDateTime.fromString(self.dbData[index.row()][index.column()], 'yyyy-MM-dd hh:mm:ss').toString(
                    'dd-MM-yyyy hh:mm:ss')
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
        """Обновляет данные в модели."""
        self.layoutAboutToBeChanged.emit()
        self.dbData = self.con.execute(self.query, [self._offset, 0]).fetchall()
        self.changePersistentIndexList(
            self.persistentIndexList(),
            [QModelIndex() for _ in range(len(self.persistentIndexList()))]
        )
        self.layoutChanged.emit()

    # def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
    #     """
    #     Args:
    #         row (int):
    #         column (int):
    #         parent (QModelIndex):
    #     """
    #     if row >= self.rowCount(parent):
    #         while row >= self.rowCount(parent):
    #             if self.canFetchMore(parent):
    #                 self.fetchMore(parent)
    #             else:
    #                 break
    #     return super().index(row, column, parent)

    def canFetchMore(self, parent: QModelIndex) -> bool:
        """
        Args:
            parent (QModelIndex):
        """
        # todo: ПЕРЕДЕЛАТЬ МЕТОД!
        try:
            self.chunkData = self.con.execute(
                self.query,
                [self.number_rows, self._offset]).fetchall()
        except sqlite3.ProgrammingError:
            # logger.exception('Exception occurred in canFetchMore')
            return False
        except sqlite3.Error:
            logger.exception('Exception sqlite query in canFetchMore')
            return False
        if self.chunkData:
            return True
        else:
            return False

    def fetchMore(self, parent: QModelIndex) -> None:
        """
        Args:
            parent (QModelIndex):
        """
        rows = len(self.dbData)
        self.beginInsertRows(QModelIndex(), rows, rows + len(self.chunkData) - 1)
        self.dbData.extend(self.chunkData)
        self._offset += len(self.chunkData)
        self.endInsertRows()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """
        Args:
            parent (QModelIndex):
        """
        if parent.isValid():
            return 0
        return len(self.dbData)

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
            self._offset -= 1
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

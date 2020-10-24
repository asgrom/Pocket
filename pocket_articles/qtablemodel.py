import typing

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt, pyqtSlot, QDateTime
from PyQt5.QtWidgets import QApplication, QWidget
import sqlite3
from . import applogger

logger = applogger.get_logger(__name__)


class TableModel(QAbstractTableModel):
    query = """select time_saved, title, id from webpages order by lower({}) {} limit ? offset ?"""

    def __init__(self, cursor: sqlite3.Cursor, number_rows=100, parent: QWidget = None):
        """
        Args:
            cursor (sqlite3.Cursor): Соединение с базой данных.
            number_rows (str): Количество строк, получаемых из базы за один запрос, (default 100)
        """
        super(TableModel, self).__init__(parent)
        self.cur = cursor
        self.number_rows = number_rows  # количество строк для считывания из базы
        self.sortColumn = 'time_saved'
        self.order = 'desc'
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
    def setCursor(self, cur: sqlite3.Cursor):
        """Устанавливает курсор базы данных.

        Устанавливаем новый курсор базы при ее смене из меню пользователя.

        Args:
            cur (sqlite3.Cursor):
        """
        self.cur = cur
        self.resetModel()

    @pyqtSlot()
    def changeSqlQuery(self, sql_query=None):
        """Изменение sql-запроса

        Если запрос не задан, поизойдет сброс на дефолтный.

        Args:
            sql_query (str): Запрос к базе данных.
        """
        self.beginResetModel()
        self.query = sql_query if sql_query else TableModel.query
        self._offset = 0
        self.dbData.clear()
        self.endResetModel()

    @pyqtSlot(int, int)
    def changeSortOrder(self, column: str, order: str):
        """Изменение сортировки.

        Args:
            order (str): Asc or Desc sorting.
            column (str): Column to be sorted.
        """
        self.beginResetModel()
        self.sortColumn = column
        self.order = order
        self.dbData.clear()
        self._offset = 0
        self.endResetModel()

    def data(self, index: QModelIndex, role: int = ...) -> typing.Any:
        """
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

    def canFetchMore(self, parent: QModelIndex) -> bool:
        """
        Args:
            parent (QModelIndex):
        """
        try:
            self.chunkData = self.cur.execute(self.query.format(self.sortColumn, self.order),
                                              [self.number_rows, self._offset]).fetchall()
        except sqlite3.ProgrammingError:
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
        return super(TableModel, self).headerData(section, orientation, role)

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

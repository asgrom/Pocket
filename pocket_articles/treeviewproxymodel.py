"""Изменяет сортировку в дереве тегов.

Сортировка происходит в названиях тегов."""
from PyQt5.QtCore import *


class TreeViewProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(TreeViewProxyModel, self).__init__(parent)
        self.setSortCaseSensitivity(Qt.CaseInsensitive)
        self.setFilterKeyColumn(0)
        self.setRecursiveFilteringEnabled(True)
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.setSortLocaleAware(True)

    def lessThan(self, leftIdx: QModelIndex, rightIdx: QModelIndex) -> bool:
        """
        Args:
            leftIdx (QModelIndex):
            rightIdx (QModelIndex):
        """
        if not leftIdx.parent().isValid() or not rightIdx.parent().isValid():
            if leftIdx.data(Qt.UserRole) == 'line' or rightIdx.data(Qt.UserRole) == 'line':
                return False
            if leftIdx.data() == 'Все статьи':
                return True
            if leftIdx.data() == 'Без тегов' and rightIdx.data() in ('Теги', 'Избранное'):
                return True
            if leftIdx.data() == 'Избранное' and rightIdx.data() == 'Теги':
                return True
            return False
        return super(TreeViewProxyModel, self).lessThan(leftIdx, rightIdx)

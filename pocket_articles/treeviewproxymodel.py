"""Изменяет сортировку в дереве тегов.

Сортировка происходит в названиях тегов."""

# todo:
#   что-то сделать с сортировкой. если отфильтровать 'избранное' слетает
#   сортировка.

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
            return leftIdx.data(Qt.UserRole + 2) < rightIdx.data(Qt.UserRole + 2)
        return super(TreeViewProxyModel, self).lessThan(leftIdx, rightIdx)

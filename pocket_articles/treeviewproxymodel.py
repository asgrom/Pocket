"""Изменяет сортировку в дереве тегов.

Сортировка происходит в названиях тегов."""

# todo:
#   что-то сделать с сортировкой. если отфильтровать 'избранное' слетает
#   сортировка.

from PyQt5.QtCore import *

AllArticles = 'all_articles'
Tags = 'tags'
Favorites = 'favorites'
NoTags = 'notags'
Line = 'line'


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
            if rightIdx.data(Qt.UserRole) == Line or leftIdx.data(Qt.UserRole) == Line:
                return False
            if leftIdx.data(Qt.UserRole) == AllArticles:
                return True
            if leftIdx.data(Qt.UserRole) == NoTags and rightIdx.data(Qt.UserRole) != AllArticles:
                return True
            if leftIdx.data(Qt.UserRole) == Favorites and rightIdx.data(Qt.UserRole) == Tags:
                return True
            return False
        return super(TreeViewProxyModel, self).lessThan(leftIdx, rightIdx)

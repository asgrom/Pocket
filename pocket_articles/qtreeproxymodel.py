from PyQt5.QtCore import *


class TreeViewProxyModel(QSortFilterProxyModel):
    def lessThan(self, leftIdx: QModelIndex, rightIdx: QModelIndex) -> bool:
        """
        Args:
            leftIdx (QModelIndex):
            rightIdx (QModelIndex):
        """
        if not leftIdx.parent().isValid() or not rightIdx.parent().isValid():
            return False
        return super(TreeViewProxyModel, self).lessThan(leftIdx, rightIdx)

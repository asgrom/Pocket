"""
    Делегат для отрисовки выделения и отрисовки линии в QTreeView
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class Delegate(QStyledItemDelegate):
    def __init__(self, *args, **kwargs):
        super(Delegate, self).__init__(*args, **kwargs)
        self.pixmap = QPixmap(':/images/hline.png')

    def paint(self, painter: QPainter, option: 'QStyleOptionViewItem', index: QModelIndex) -> None:
        if index.data(Qt.UserRole) == 'line':
            rect = option.rect
            rect.setX(0)
            painter.drawPixmap(rect.x(), rect.y() + (rect.height() - self.pixmap.height()) // 2,
                               rect.width() - 5, self.pixmap.height(), self.pixmap)
            return

        # если элемент выделен делаем жирный шрифт
        if option.state & QStyle.State_Selected:
            option.rect.setWidth(option.rect.width() - 5)

        if index.data(Qt.UserRole + 1) is not None:
            fm = option.fontMetrics
            rect = option.rect
            painter.save()
            painter.drawText(15 + rect.x() + fm.width(index.data(Qt.DisplayRole)), rect.y(),
                             rect.width() - 15 - fm.width(index.data(Qt.DisplayRole)), rect.height(),
                             int(Qt.AlignLeft | Qt.AlignVCenter), f'({index.data(Qt.UserRole + 1)})')
            painter.restore()

        super(Delegate, self).paint(painter, option, index)

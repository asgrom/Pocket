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
            dx = 5
            pen = QPen()
            pen.setWidthF(0.5)
            pen.setColor(QColor(63, 63, 63))
            painter.setPen(pen)
            painter.drawLine(QLineF(
                    dx,
                    rect.y() + rect.height() / 2,
                    rect.width() + rect.x() - dx,
                    rect.y() + rect.height() / 2
                    ))
            return

        # уменьшаем ширину выделения
        if option.state & QStyle.State_Selected:
            option.rect.setWidth(option.rect.width() - 5)

        # дописывает количесво статей в строку с тегом
        if index.data(Qt.UserRole + 1) is not None:
            fm = option.fontMetrics
            rect = option.rect
            painter.drawText(rect.x() + fm.width(index.data(Qt.DisplayRole) + '    '), rect.y(),
                             fm.width(f'({index.data(Qt.UserRole + 1)})'), rect.height(),
                             Qt.AlignLeft | Qt.AlignVCenter, f'({index.data(Qt.UserRole + 1)})')
            # painter.drawText(15 + rect.x() + fm.width(index.data(Qt.DisplayRole)), rect.y(),
            #                  rect.width() - 15 - fm.width(index.data(Qt.DisplayRole)), rect.height(),
            #                  int(Qt.AlignLeft | Qt.AlignVCenter), f'({index.data(Qt.UserRole + 1)})')

        super(Delegate, self).paint(painter, option, index)

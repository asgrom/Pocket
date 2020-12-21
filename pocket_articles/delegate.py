"""
    Делегат для отрисовки выделения и отрисовки линии в QTreeView
"""

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class Delegate(QStyledItemDelegate):
    def __init__(self, *args, **kwargs):
        super(Delegate, self).__init__(*args, **kwargs)
        self.pixmap = QPixmap(':/images/hline.png')

    def paint(self, painter: QPainter, option: 'QStyleOptionViewItem', index: QModelIndex) -> None:
        rect = option.rect

        # на сколько сдвигаем границу по осям
        dx = 5
        dy = 2

        ######################################################################
        # рисуем линию
        if index.data(Qt.UserRole) == 'line':
            pen = QPen()
            pen.setWidthF(1.0)
            pen.setColor(QColor(255, 170, 80, 255))
            painter.setPen(pen)
            painter.drawLine(QLineF(
                dx,
                rect.y() + (rect.height() - 1) / 2,
                rect.width() - 1 + rect.x() - dx,
                rect.y() + (rect.height() - 1) / 2
            ))
            return

        painter.setRenderHints(QPainter.TextAntialiasing | QPainter.Antialiasing, True)

        ######################################################################
        # рисуем градиент вокруг выделенного текста
        if option.state & QStyle.State_Selected:
            selectionRect = QRect(rect)
            selectionRect.setX(dx)
            selectionRect.setWidth(selectionRect.width() - dx)
            selectionRect.setY(selectionRect.y() + dy)
            selectionRect.setHeight(selectionRect.height() - dy)

            x, y, w, h = (selectionRect.x(), selectionRect.y(),
                          selectionRect.width(), selectionRect.height())

            gradient = QLinearGradient(x, y, x, y + h - 1)
            gradient.setColorAt(0, QColor(255, 170, 80, 76))
            gradient.setColorAt(0.5, QColor(255, 170, 80, 152))
            gradient.setColorAt(1, QColor(255, 170, 80, 255))

            painter.setPen(Qt.NoPen)
            painter.setBrush(gradient)
            painter.drawRoundedRect(selectionRect, 10, 10)

        ######################################################################
        # рисуем иконку
        if index.data(Qt.DecorationRole) is not None:
            opt = QStyleOptionViewItem(option)
            iconSize = opt.decorationSize
            icon = index.data(Qt.DecorationRole)
            painter.drawPixmap(
                rect.x(),
                rect.y() + (rect.height() - iconSize.height()) // 2 - 1,
                QPixmap(icon.pixmap(iconSize)))
            rect.setX(rect.x() + iconSize.width() + 5)

        ######################################################################
        # получаем текст с разрывом, если он не помещается в область
        if index.data(Qt.UserRole + 1) is not None:
            elidedText = option.fontMetrics.elidedText(
                index.data() + '    ' + f'({index.data(Qt.UserRole + 1)})',
                Qt.ElideRight, rect.width() - 2 * dx
            )
        else:
            elidedText = option.fontMetrics.elidedText(
                index.data(), Qt.ElideRight, rect.width() - 2 * dx
            )


        painter.setPen(QColor(63, 63, 63))
        painter.drawText(rect, Qt.AlignVCenter, elidedText)

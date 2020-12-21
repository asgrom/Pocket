"""
    Стиль для отображения элементов в QTreeView.

    Переопределяет отображение примитивов (веток, выделение...) в QTreeView.
"""
import typing

from PyQt5 import QtGui
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class ProxyStyle(QProxyStyle):
    def drawPrimitive(self, element: QStyle.PrimitiveElement, option: 'QStyleOption',
                      painter: QtGui.QPainter, widget: typing.Optional[QWidget] = ...) -> None:

        """
        Args:
            element (QStyle.PrimitiveElement):
            option:
            painter (QtGui.QPainter):
            widget:
        """
        # убираем фокусную рамку
        if element == QStyle.PE_FrameFocusRect:
            return
        if element == QStyle.PE_PanelItemViewItem:
            return
        if isinstance(widget, QTreeView):
            if element == QStyle.PE_PanelItemViewItem:
                return
            if element == QStyle.PE_PanelItemViewRow:
                return

        super(ProxyStyle, self).drawPrimitive(element, option, painter, widget)

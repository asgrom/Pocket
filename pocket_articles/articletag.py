from PyQt5.QtCore import pyqtSlot, QCoreApplication, QEvent
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QLineEdit, QSizePolicy

_QSS = """
    QLineEdit {
        background-color: palette(window);
        border-radius: 10px;
        border-style: outset;
        border-width: 1px;
        border-color: darkgrey;
        padding-left: 5px;
    }"""


class DeleteArticleTagEvent(QEvent):
    """Событие удаления тега страницы"""
    idType = QEvent.registerEventType()

    def __init__(self, tag: str):
        """
        Args:
            tag (str): Тег статьи.
        """
        # noinspection PyTypeChecker
        QEvent.__init__(self, DeleteArticleTagEvent.idType)
        self.tag = tag


class ArticleTag(QLineEdit):
    """Класс строки ввода. Отображает теги статьи"""

    def __init__(self, *args, **kwargs):
        """
        Args:
            *args:
            **kwargs:
        """
        super().__init__(*args, **kwargs)
        icon = QIcon(QPixmap(':/images/window-close.png').scaledToWidth(16))
        self.setReadOnly(True)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.setFrame(False)

        fm = self.fontMetrics()
        width = fm.width(self.text())  # ширина строки в пикселах
        self.setFixedWidth(width + 34 + 5)
        # self.setStyleSheet(_QSS)
        # вставляем иконку действия
        # noinspection PyNoneFunctionAssignment
        self.deleteAction = self.addAction(icon, QLineEdit.TrailingPosition)
        self.deleteAction.triggered.connect(self.action_triggered)

    # noinspection PyTypeChecker
    @pyqtSlot()
    def action_triggered(self):
        # Чтобы передать событие основному окну пришлось использовать метод виджета nativeParentWidget()
        QCoreApplication.sendEvent(self.nativeParentWidget(), DeleteArticleTagEvent(self.text()))
        self.deleteLater()

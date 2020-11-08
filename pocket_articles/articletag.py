from PyQt5.QtCore import pyqtSlot, QCoreApplication, QEvent
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QLineEdit, QSizePolicy

_QSS = """
    QLineEdit {
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgb(215,215,215), stop:1 beige);
        border-radius: 10px;
        border-style: inset;
        border-width: 1px;
        border-color: grey;
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
        icon = QIcon(':/images/close-circle.svg')
        self.setReadOnly(True)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.setFrame(False)

        fm = self.fontMetrics()
        width = fm.width(self.text())  # ширина строки в пикселах
        self.setFixedWidth(width + 34 + 5)
        self.setStyleSheet(_QSS)
        # вставляем иконку действия
        # noinspection PyNoneFunctionAssignment
        self.deleteAction = self.addAction(icon, QLineEdit.TrailingPosition)
        self.deleteAction.triggered.connect(self.action_triggered)

    @pyqtSlot()
    def action_triggered(self):
        # noinspection PyTypeChecker
        QCoreApplication.sendEvent(self.parent(), DeleteArticleTagEvent(self.text()))
        self.deleteLater()

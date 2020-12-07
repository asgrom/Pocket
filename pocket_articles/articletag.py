from PyQt5.QtCore import pyqtSlot, QCoreApplication, QEvent
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QLineEdit, QSizePolicy

_QSS = """
    QLineEdit {
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(166, 166, 166, 0.2),
        stop:0.5 rgba(166, 166, 166, 0.0),
        stop:1 rgba(166, 166, 166, 0.2));
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

    # noinspection PyTypeChecker
    @pyqtSlot()
    def action_triggered(self):
        # Чтобы передать событие основному окну пришлось использовать метод виджета nativeParentWidget()
        QCoreApplication.sendEvent(self.nativeParentWidget(), DeleteArticleTagEvent(self.text()))
        self.deleteLater()

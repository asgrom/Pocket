from PyQt5.QtCore import pyqtSlot, QCoreApplication, QEvent
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QLineEdit, QSizePolicy


class DeleteArticleTagEvent(QEvent):
    """Событие удаления тега страницы"""
    idType = QEvent.registerEventType()

    def __init__(self, tag: str):
        """
        Args:
            tag (str): Тег статьи.
        """
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
        self.setFixedWidth(width + 34)
        self.setStyleSheet('QLineEdit {background: transparent; border: none;}')
        # вствляем иконку действия
        self.deleteAction = self.addAction(icon, QLineEdit.TrailingPosition)
        self.deleteAction.triggered.connect(self.action_triggered)

    @pyqtSlot()
    def action_triggered(self):
        QCoreApplication.sendEvent(self.parent(), DeleteArticleTagEvent(self.text()))
        self.deleteLater()

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class Dialog(QDialog):
    """Класс для получения от пользователя имени файла базы данных

    Чтобы не создавать отдельный экземпляр класса, можно использовать
    статический метод getDatabaseFile. """

    databaseFile = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.connectSlots()

    def initUI(self):
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.resize(400, 200)

        self.label = QLabel('Нет существующей базы.\nУкажите базу данных.')
        self.label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        self.createBtn = QPushButton('Создать')
        self.openBtn = QPushButton('Открыть')

        hbox = QHBoxLayout()
        hbox.addStretch()
        hbox.addWidget(self.createBtn)
        hbox.addWidget(self.openBtn)

        vbox = QVBoxLayout(self)
        vbox.addWidget(self.label)
        vbox.addLayout(hbox)

    def connectSlots(self):
        self.createBtn.clicked.connect(self.getSaveDatabaseFile)
        self.openBtn.clicked.connect(self.getExistingDatabaseFile)

    def getExistingDatabaseFile(self):
        """Получаем имя файла существующей базы данных."""

        path, _ = QFileDialog.getOpenFileName(
            self, 'Database File',
            QStandardPaths.writableLocation(QStandardPaths.HomeLocation),
            filter='SQLite (*.sql *.db *.sqlite);;All (*.*)'
        )
        Dialog.databaseFile = path
        if path:
            self.done(QDialog.Accepted)
        else:
            self.done(QDialog.Rejected)

    def getSaveDatabaseFile(self):
        """Получаем имя файла для новой базы данных."""

        path, _ = QFileDialog.getSaveFileName(
            self, 'Create Database File',
            QStandardPaths.writableLocation(QStandardPaths.HomeLocation),
            filter='SQLite (*.db *.sqlite *.sql);;All (*.*)'
        )
        if path:
            if QFileInfo(path).suffix() != 'db':
                Dialog.databaseFile = path + '.db'
            self.done(QDialog.Accepted)
        else:
            self.done(QDialog.Rejected)

    @staticmethod
    def getDatabaseFile(parent) -> str:
        """Получить имя файла базы данных.

        Создается диалог, с которым воздействует пользователь.
        Метод возвращает имя файла базы данных."""

        dlg = Dialog(parent)
        dlg.exec()
        return Dialog.databaseFile

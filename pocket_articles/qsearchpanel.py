from PyQt5.QtCore import pyqtSignal, Qt, pyqtSlot
from PyQt5.QtGui import QKeySequence, QShowEvent, QIcon
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtWidgets import QWidget, QSizePolicy, QHBoxLayout, QPushButton, QCheckBox, QLineEdit, QShortcut

from . import applogger
# noinspection PyUnresolvedReferences
from . import resources

logger = applogger.get_logger(__name__)


_QSS = """
    QLineEdit {
        border-radius: 10px;
        border-style: inset;
        border-width: 1px;
        border-color: rgba(83, 145, 222, 0.8);
        /*padding: 0 8px;*/
    }
    QPushButton {
        border-style: none;
        border-width: 1px;
        padding-top: 4px;
        padding-bottom: 4px;
        padding-right: 5px;
        padding-left: 5px;
        border-radius: 10px;
        border-color: grey;
    }
    QPushButton:hover:pressed {
        border-style: inset;
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgb(215,215,215), stop:1 beige);
    }
    QPushButton:hover {
        border-style: outset;
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 beige, stop:1 rgb(215,215,215));
    }"""


class SearchPanel(QWidget):
    searched = pyqtSignal(str, QWebEnginePage.FindFlag)

    def __init__(self, parent=None):
        """
        Args:
            parent:
        """
        super(SearchPanel, self).__init__(parent)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.setStyleSheet(_QSS)

        hbox = QHBoxLayout(self)
        hbox.setContentsMargins(0, 0, 0, 0)

        icon_close = QIcon(':/images/close-circle.svg')
        icon_back = QIcon(':/images/iconfinder_old-edit-undo_23492.png')
        icon_forward = QIcon(':/images/iconfinder_old-edit-redo_23491.png')

        self.nextBtn = QPushButton(icon_forward, 'Следующее')
        self.nextBtn.clicked.connect(self.search)

        self.prevBtn = QPushButton(icon_back, 'Предыдущее')
        self.prevBtn.clicked.connect(lambda: self.search(QWebEnginePage.FindBackward))

        self.caseSensitively = QCheckBox('Учитывать регистр')

        self.search_le = QLineEdit()
        self.search_le.addAction(QIcon(':/images/search-50.svg'), QLineEdit.LeadingPosition)
        self.search_le.setClearButtonEnabled(True)

        self.closeBtn = QPushButton(icon_close, '')
        self.closeBtn.clicked.connect(self.hide_widget)

        hbox.addStretch(1)
        hbox.addWidget(self.closeBtn)
        hbox.addWidget(self.search_le, 1)
        hbox.addWidget(self.prevBtn)
        hbox.addWidget(self.nextBtn)
        hbox.addWidget(self.caseSensitively)

        QShortcut(Qt.Key_Escape, self, self.hide_widget)
        QShortcut(Qt.Key_F3, self, self.search)
        QShortcut(QKeySequence.FindNext, self, self.search)
        QShortcut(QKeySequence.FindPrevious, self, lambda: self.search(QWebEnginePage.FindBackward))
        QShortcut(QKeySequence(Qt.SHIFT + Qt.Key_F3), self, lambda: self.search(QWebEnginePage.FindBackward))

        self.setFocusProxy(self.search_le)

        self.search_le.returnPressed.connect(self.search)
        self.search_le.textChanged.connect(self.search)

    @pyqtSlot()
    def hide_widget(self):
        self.search_le.clear()
        self.hide()

    @pyqtSlot()
    def search(self, flag: QWebEnginePage.FindFlag = None):
        """
        Args:
            flag (QWebEnginePage.FindFlag):
        """
        if not flag:
            flag = QWebEnginePage.FindFlag()
        if self.caseSensitively.isChecked():
            flag |= QWebEnginePage.FindCaseSensitively
        self.searched.emit(self.search_le.text(), flag)

    def showEvent(self, a0: QShowEvent) -> None:
        """
        Args:
            a0 (QShowEvent):
        """
        super(SearchPanel, self).showEvent(a0)
        self.setFocus(Qt.ShortcutFocusReason)

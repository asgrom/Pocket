from PyQt5.QtWidgets import QComboBox, QSizePolicy


_QSS = """
    QComboBox {
        border-width: 1px;
        border-color: grey;
        border-radius: 9px;
        border-style: outset;
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 beige, stop:1 rgb(215,215,215));
    }
    QComboBox QAbstractItemView {
        border: 0px outset gray;
        selection-background-color: rgba(255, 170, 80, 1);
    }
    QComboBox:on { /* shift the text when the popup opens */
        padding-top: 6px;
        padding-left: 8px;
        border-style: inset;
    }
    /* QComboBox gets the "on" state when the popup is open */
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 15px;
        border-width: 0px;
        border-top-right-radius: 9px; /* same radius as the QComboBox */
        border-bottom-right-radius: 9px;
    }
    QComboBox::down-arrow {
        image: url(:/images/arrow-down.png)
    }
    """


class TagsComboBox(QComboBox):
    """Комбобокс со списком тегов"""

    defaultText = 'Add article tag'

    def __init__(self, parent=None):
        """
        Args:
            parent:
        """
        super(TagsComboBox, self).__init__(parent)
        self.setEditable(True)
        self.lineEdit().setPlaceholderText(self.defaultText)
        self.lineEdit().setClearButtonEnabled(True)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.setInsertPolicy(QComboBox.InsertAlphabetically)
        # noinspection PyUnresolvedReferences
        self.activated.connect(self.on_activated)
        self.setStyleSheet(_QSS)
        self.lineEdit().setStyleSheet(
                'background: transparent;'
                'border-top-left-radius: 9px;'
                'border-bottom-left-radius: 9px;'
                'padding-left: 5px;'
                )

    def on_activated(self):
        self.setCurrentIndex(-1)

    def showPopup(self):
        """расширяет всплывающее окно до ширины элементов"""
        self.view().setMinimumWidth(self.view().sizeHintForColumn(0))
        super().showPopup()

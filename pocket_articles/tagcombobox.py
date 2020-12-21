from PyQt5.QtWidgets import QComboBox, QSizePolicy


class TagsComboBox(QComboBox):
    """Комбобокс со списком тегов"""

    defaultText = 'Add tag'

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

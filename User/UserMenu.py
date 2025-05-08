from header import *
from Shared.ScriptsPage import ScriptsPage
from Shared.BalancePage import BalancePage


class UserMenu(QDialog):
    def __init__(self, db_connection, parent=None):
        super().__init__(parent)
        loadUi(r'UI\UserMenu.ui', self)
        self.db_connection = db_connection
        self.parent = parent

        self.btn_scripts.clicked.connect(self.open_scripts)
        self.btn_balance.clicked.connect(self.open_balance)
        self.btn_close.clicked.connect(self.back)

    def open_scripts(self):
        self.hide()
        scripts_page = ScriptsPage(self.db_connection)
        scripts_page.exec_()
        self.show()

    def open_balance(self):
        self.hide()
        balance_page = BalancePage(self.db_connection)
        balance_page.exec_()
        self.show()

    def back(self):
        self.hide()
        if self.parent:
            self.parent.show()
        if self.db_connection:
            self.db_connection.close()
from header import *
from Admin.AdminsPage import AdminsPage
from Shared.BalancePage import BalancePage
from Admin.DishesPage import DishesPage
from Admin.IngredientsPage import IngredientsPage
from Admin.PlansPage import PlansPage
from Admin.RecipesPage import RecipesPage
from Shared.ScriptsPage import ScriptsPage
from Admin.StoragePage import StoragePage


class AdminMenu(QDialog):
    def __init__(self, db_connection, login_page):
        super().__init__()
        loadUi('UI\AdminMenu.ui', self)
        self.login_page = login_page
        self.db_connection = db_connection
        self.setup_buttons()

    def setup_buttons(self):
        # Кнопки раздела "Редактировать"
        self.btn_admins.clicked.connect(lambda: self.open_page(AdminsPage))
        self.btn_plans.clicked.connect(lambda: self.open_page(PlansPage))
        self.btn_dishes.clicked.connect(lambda: self.open_page(DishesPage))
        self.btn_recipes.clicked.connect(lambda: self.open_page(RecipesPage))
        self.btn_ingredients.clicked.connect(lambda: self.open_page(IngredientsPage))
        self.btn_storage.clicked.connect(lambda: self.open_page(StoragePage))

        # Кнопки раздела "Формы"
        self.btn_scripts.clicked.connect(lambda: self.open_page(ScriptsPage))
        self.btn_balance.clicked.connect(lambda: self.open_page(BalancePage))

        # Кнопка закрытия
        self.btn_close.clicked.connect(self.back)

    def show_stub(self, page_name):
        QMessageBox.information(self, "Заглушка", f"Должно открыться окно: {page_name}")

    def back(self):
        self.hide()
        if self.login_page:
            self.login_page.show()
        if self.db_connection:
            self.db_connection.close()

    def open_page(self, page_class):
        try:
            page = page_class(self.db_connection)
            page.exec_()
        except Exception as e:
            print(e)

from header import *
from Admin.AdminMenu import AdminMenu
from User.UserMenu import UserMenu


class LoginPage(QDialog):
    def __init__(self):
        super().__init__()
        loadUi('UI\LoginPage.ui', self)
        self.btn_enter.clicked.connect(self.authenticate)
        self.db_connection = None  # Для хранения подключения

        self.db_config = {
            "host": "localhost",
            "database": "menu_planning",
            "user": "application",
            "password": "app"
        }

    def authenticate(self):
        username = self.le_username.text().strip()
        password = self.le_password.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return

        try:
            # Устанавливаем соединение
            self.db_connection = psycopg2.connect(**self.db_config)
            cursor = self.db_connection.cursor()

            cursor.execute("""
                SELECT role FROM users 
                WHERE username = %s AND password = %s
            """, (username, password))

            result = cursor.fetchone()
            cursor.close()

            if result:
                role = result[0]
                self.open_menu(role)
            else:
                QMessageBox.critical(self, "Ошибка", "Неверный логин или пароль!")

        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка БД", f"Ошибка: {str(e)}")
            if self.db_connection:
                self.db_connection.close()

    def open_menu(self, role):
        try:
            db_connection = psycopg2.connect(**self.db_config)

            if role == "admin":
                admin_menu = AdminMenu(db_connection, self)
                admin_menu.exec_()
            elif role == "user":
                user_menu = UserMenu(db_connection, self)
                user_menu.exec_()

            db_connection.close()

            self.show()

        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка БД", f"Ошибка подключения: {str(e)}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    login_dialog = LoginPage()
    login_dialog.show()
    app.exec_()
from header import *


class AdminsPage(QDialog):
    def __init__(self, db_connection):
        super().__init__()
        loadUi('UI\AdminsPage.ui', self)
        self.db_connection = db_connection
        self.selected_id = None

        # Настройка таблицы
        self.tableWidget.setColumnWidth(0, 250)
        self.tableWidget.setColumnWidth(1, 150)
        self.tableWidget.setColumnWidth(2, 100)

        # Подключение кнопок
        self.btn_add.clicked.connect(self.add_admin)
        self.btn_edit.clicked.connect(self.edit_admin)
        self.btn_delete.clicked.connect(self.delete_admin)
        self.tableWidget.itemSelectionChanged.connect(self.load_selected_row)

        # Загрузка данных
        self.load_data()

    def load_data(self):
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT adminid, full_name, phone, salary FROM admins")
            data = cursor.fetchall()

            self.tableWidget.setRowCount(len(data))
            for row_idx, row_data in enumerate(data):
                for col_idx, value in enumerate(row_data[1:]):  # Пропускаем adminid
                    item = QTableWidgetItem(str(value))
                    if col_idx == 0:  # Сохраняем ID только в первой ячейке
                        item.setData(1000, row_data[0])
                    self.tableWidget.setItem(row_idx, col_idx, item)

            cursor.close()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки: {str(e)}")

    def load_selected_row(self):
        selected = self.tableWidget.selectedItems()
        if not selected:
            return

        # Получаем номер строки и все элементы строки
        row = selected[0].row()
        row_items = [
            self.tableWidget.item(row, col)
            for col in range(self.tableWidget.columnCount())
        ]

        # Проверяем, что все ячейки строки выбраны
        if None in row_items:
            QMessageBox.warning(self, "Ошибка", "Выберите всю строку")
            return

        # Заполняем поля данными из строки
        self.le_full_name.setText(row_items[0].text())
        self.le_phone.setText(row_items[1].text())
        self.le_salary.setText(row_items[2].text())

        # Получаем ID из скрытых данных первой ячейки
        self.selected_id = row_items[0].data(1000)

    def validate_fields(self):
        try:
            if not self.le_full_name.text().strip():
                raise ValueError("ФИО не может быть пустым")
            if not self.le_salary.text().isdigit() or int(self.le_salary.text()) <= 0:
                raise ValueError("Некорректная зарплата")
            return True
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка", str(e))
            return False

    def add_admin(self):
        if not self.validate_fields():
            return

        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                INSERT INTO admins (full_name, phone, salary)
                VALUES (%s, %s, %s)
            """, (
                self.le_full_name.text().strip(),
                self.le_phone.text().strip(),
                int(self.le_salary.text())
            ))
            self.db_connection.commit()
            self.load_data()

        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка добавления: {str(e)}")

    def edit_admin(self):
        if not self.selected_id:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для редактирования")
            return

        if not self.validate_fields():
            return

        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                UPDATE admins 
                SET full_name = %s, phone = %s, salary = %s
                WHERE adminid = %s
            """, (
                self.le_full_name.text().strip(),
                self.le_phone.text().strip(),
                int(self.le_salary.text()),
                self.selected_id
            ))
            self.db_connection.commit()
            self.load_data()

        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка редактирования: {str(e)}")

    def delete_admin(self):
        if not self.selected_id:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для удаления")
            return

        try:
            cursor = self.db_connection.cursor()
            cursor.execute("DELETE FROM admins WHERE adminid = %s", (self.selected_id,))
            self.db_connection.commit()
            self.load_data()

        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка удаления: {str(e)}")
from header import *


class IngredientsPage(QDialog):
    def __init__(self, db_connection):
        super().__init__()
        loadUi('UI\IngredientsPage.ui', self)
        self.db_connection = db_connection
        self.selected_id = None

        self.tableWidget.setColumnWidth(0, 500)

        self.btn_add.clicked.connect(self.add_ingredient)
        self.btn_edit.clicked.connect(self.edit_ingredient)
        self.btn_delete.clicked.connect(self.delete_ingredient)
        self.tableWidget.itemSelectionChanged.connect(self.load_selected_row)

        self.load_data()

    def load_data(self):
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT ingrid, ingr_name FROM ingredients")
            data = cursor.fetchall()

            self.tableWidget.setRowCount(len(data))
            for row_idx, row_data in enumerate(data):
                item = QTableWidgetItem(row_data[1])
                item.setData(1000, row_data[0])  # Сохраняем ID в данных ячейки
                self.tableWidget.setItem(row_idx, 0, item)

            cursor.close()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных: {str(e)}")

    def load_selected_row(self):
        selected = self.tableWidget.selectedItems()
        if not selected:
            return

        # Получаем ID и название из выбранной строки
        self.selected_id = selected[0].data(1000)
        self.le_ingr_name.setText(selected[0].text())

    def validate_fields(self):
        if not self.le_ingr_name.text().strip():
            QMessageBox.warning(self, "Ошибка", "Название не может быть пустым")
            return False
        return True

    def add_ingredient(self):
        if not self.validate_fields():
            return

        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                INSERT INTO ingredients (ingr_name)
                VALUES (%s)
            """, (self.le_ingr_name.text().strip(),))
            self.db_connection.commit()
            self.load_data()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка добавления: {str(e)}")

    def edit_ingredient(self):
        if not self.selected_id:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для редактирования")
            return

        if not self.validate_fields():
            return

        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                UPDATE ingredients 
                SET ingr_name = %s 
                WHERE ingrid = %s
            """, (self.le_ingr_name.text().strip(), self.selected_id))
            self.db_connection.commit()
            self.load_data()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка редактирования: {str(e)}")

    def delete_ingredient(self):
        if not self.selected_id:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для удаления")
            return

        try:
            cursor = self.db_connection.cursor()

            # Проверка использования в других таблицах
            cursor.execute("SELECT 1 FROM cooking WHERE ingrid = %s LIMIT 1", (self.selected_id,))
            if cursor.fetchone():
                QMessageBox.warning(self, "Ошибка", "Ингредиент используется в рецептах")
                return

            cursor.execute("SELECT 1 FROM storages WHERE ingrid = %s LIMIT 1", (self.selected_id,))
            if cursor.fetchone():
                QMessageBox.warning(self, "Ошибка", "Ингредиент есть на складе")
                return

            cursor.execute("DELETE FROM ingredients WHERE ingrid = %s", (self.selected_id,))
            self.db_connection.commit()
            self.load_data()

        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка удаления: {str(e)}")
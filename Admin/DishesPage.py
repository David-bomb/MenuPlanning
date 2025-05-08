from header import *

class DishesPage(QDialog):
    def __init__(self, db_connection):
        super().__init__()
        loadUi('UI\DishesPage.ui', self)
        self.db_connection = db_connection
        self.selected_id = None

        self.tableWidget.setColumnWidth(0, 300)
        self.tableWidget.setColumnWidth(1, 150)
        self.tableWidget.setColumnWidth(2, 150)

        self.btn_add.clicked.connect(self.add_dish)
        self.btn_edit.clicked.connect(self.edit_dish)
        self.btn_delete.clicked.connect(self.delete_dish)
        self.tableWidget.itemSelectionChanged.connect(self.load_selected_row)

        self.load_data()

    def load_data(self):
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT dishid, dish_name, weight, price FROM dishes")
            data = cursor.fetchall()

            self.tableWidget.setRowCount(len(data))
            for row_idx, row_data in enumerate(data):
                self.tableWidget.setItem(row_idx, 0, QTableWidgetItem(row_data[1]))
                self.tableWidget.setItem(row_idx, 1, QTableWidgetItem(str(row_data[2])))
                self.tableWidget.setItem(row_idx, 2, QTableWidgetItem(str(row_data[3])))
                self.tableWidget.item(row_idx, 0).setData(1000, row_data[0])  # Сохраняем ID

            cursor.close()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных: {str(e)}")

    def load_selected_row(self):
        selected = self.tableWidget.selectedItems()
        if not selected:
            return

        # Проверка выбора всей строки
        row = selected[0].row()
        row_items = [
            self.tableWidget.item(row, col)
            for col in range(self.tableWidget.columnCount())
        ]
        if None in row_items:
            QMessageBox.warning(self, "Ошибка", "Выберите всю строку")
            return

        # Заполнение полей
        self.le_dish_name.setText(row_items[0].text())
        self.le_weight.setText(row_items[1].text())
        self.le_price.setText(row_items[2].text())
        self.selected_id = row_items[0].data(1000)

    def validate_fields(self):
        try:
            if not self.le_dish_name.text().strip():
                raise ValueError("Название блюда не может быть пустым")
            if not self.le_weight.text().isdigit() or int(self.le_weight.text()) <= 0:
                raise ValueError("Вес должен быть положительным числом")
            if not self.le_price.text().isdigit() or int(self.le_price.text()) <= 0:
                raise ValueError("Цена должна быть положительным числом")
            return True
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка", str(e))
            return False

    def add_dish(self):
        if not self.validate_fields():
            return

        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                INSERT INTO dishes (dish_name, weight, price)
                VALUES (%s, %s, %s)
            """, (
                self.le_dish_name.text().strip(),
                int(self.le_weight.text()),
                int(self.le_price.text())
            ))
            self.db_connection.commit()
            self.load_data()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка добавления: {str(e)}")

    def edit_dish(self):
        if not self.selected_id:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для редактирования")
            return

        if not self.validate_fields():
            return

        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                UPDATE dishes 
                SET dish_name = %s, weight = %s, price = %s
                WHERE dishid = %s
            """, (
                self.le_dish_name.text().strip(),
                int(self.le_weight.text()),
                int(self.le_price.text()),
                self.selected_id
            ))
            self.db_connection.commit()
            self.load_data()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка редактирования: {str(e)}")

    def delete_dish(self):
        if not self.selected_id:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для удаления")
            return

        try:
            cursor = self.db_connection.cursor()
            cursor.execute("DELETE FROM dishes WHERE dishid = %s", (self.selected_id,))
            self.db_connection.commit()
            self.load_data()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка удаления: {str(e)}")
from header import *


class RecipesPage(QDialog):
    def __init__(self, db_connection):
        super().__init__()
        loadUi('UI\RecipesPage.ui', self)
        self.db_connection = db_connection
        self.selected_id = None

        self.setup_comboboxes()

        self.tableWidget.setColumnWidth(0, 300)
        self.tableWidget.setColumnWidth(1, 300)
        self.tableWidget.setColumnWidth(2, 150)

        self.btn_add.clicked.connect(self.add_recipe)
        self.btn_edit.clicked.connect(self.edit_recipe)
        self.btn_delete.clicked.connect(self.delete_recipe)
        self.tableWidget.itemSelectionChanged.connect(self.load_selected_row)

        self.load_data()

    def setup_comboboxes(self):
        self.cb_dish.setEditable(True)
        self.cb_dish.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.cb_dish.completer().setFilterMode(Qt.MatchContains)

        self.cb_ingredient.setEditable(True)
        self.cb_ingredient.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.cb_ingredient.completer().setFilterMode(Qt.MatchContains)

        self.load_dishes()
        self.load_ingredients()

    def load_dishes(self):
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT dishid, dish_name FROM dishes")
            dishes = cursor.fetchall()

            self.cb_dish.clear()
            for dish_id, dish_name in dishes:
                self.cb_dish.addItem(dish_name, dish_id)

            cursor.close()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки блюд: {str(e)}")

    def load_ingredients(self):
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT ingrid, ingr_name FROM ingredients")
            ingredients = cursor.fetchall()

            self.cb_ingredient.clear()
            for ingr_id, ingr_name in ingredients:
                self.cb_ingredient.addItem(ingr_name, ingr_id)

            cursor.close()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки ингредиентов: {str(e)}")

    def load_data(self):
        try:
            cursor = self.db_connection.cursor()
            query = """
                SELECT c.dishid, c.ingrid, c.quantity, 
                       d.dish_name, i.ingr_name 
                FROM cooking c
                JOIN dishes d ON c.dishid = d.dishid
                JOIN ingredients i ON c.ingrid = i.ingrid
            """
            cursor.execute(query)
            data = cursor.fetchall()

            self.tableWidget.setRowCount(len(data))
            for row_idx, row_data in enumerate(data):
                self.tableWidget.setItem(row_idx, 0, QTableWidgetItem(row_data[3]))
                self.tableWidget.setItem(row_idx, 1, QTableWidgetItem(row_data[4]))
                self.tableWidget.setItem(row_idx, 2, QTableWidgetItem(str(row_data[2])))
                self.tableWidget.item(row_idx, 0).setData(1000, (row_data[0], row_data[1]))  # Сохраняем ID

            cursor.close()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки рецептов: {str(e)}")

    def load_selected_row(self):
        selected = self.tableWidget.selectedItems()
        if not selected:
            return

        row = selected[0].row()
        try:
            # Получаем ID из данных первой ячейки (dishid, ingrid)
            self.selected_id = self.tableWidget.item(row, 0).data(1000)

            # Устанавливаем значения в ComboBox
            dish_name = self.tableWidget.item(row, 0).text()
            ingr_name = self.tableWidget.item(row, 1).text()

            self.cb_dish.setCurrentText(dish_name)
            self.cb_ingredient.setCurrentText(ingr_name)

            # Устанавливаем количество
            self.le_quantity.setText(self.tableWidget.item(row, 2).text())

        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка выбора строки: {str(e)}")

    def validate_fields(self):
        try:
            if not self.le_quantity.text().isdigit():
                raise ValueError("Количество должно быть числом")
            if int(self.le_quantity.text()) <= 0:
                raise ValueError("Количество должно быть больше 0")
            if self.cb_dish.currentData() is None:
                raise ValueError("Выберите блюдо")
            if self.cb_ingredient.currentData() is None:
                raise ValueError("Выберите ингредиент")
            return True
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка", str(e))
            return False

    def add_recipe(self):
        if not self.validate_fields():
            return

        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                INSERT INTO cooking (dishid, ingrid, quantity)
                VALUES (%s, %s, %s)
            """, (
                self.cb_dish.currentData(),
                self.cb_ingredient.currentData(),
                int(self.le_quantity.text())
            ))
            self.db_connection.commit()
            self.load_data()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка добавления: {str(e)}")

    def edit_recipe(self):
        if not self.selected_id:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для редактирования")
            return

        if not self.validate_fields():
            return

        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                UPDATE cooking 
                SET dishid = %s, ingrid = %s, quantity = %s 
                WHERE dishid = %s AND ingrid = %s
            """, (
                self.cb_dish.currentData(),
                self.cb_ingredient.currentData(),
                int(self.le_quantity.text()),
                self.selected_id[0],
                self.selected_id[1]
            ))
            self.db_connection.commit()
            self.load_data()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка редактирования: {str(e)}")

    def delete_recipe(self):
        if not self.selected_id:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для удаления")
            return

        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                DELETE FROM cooking 
                WHERE dishid = %s AND ingrid = %s
            """, (self.selected_id[0], self.selected_id[1]))
            self.db_connection.commit()
            self.load_data()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка удаления: {str(e)}")
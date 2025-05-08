from header import *

class StoragePage(QDialog):
    def __init__(self, db_connection):
        super().__init__()
        loadUi('UI\StoragePage.ui', self)
        self.db_connection = db_connection
        self.selected_id = None

        self.de_date.setDate(QDate.currentDate())
        self.setup_combobox()
        self.setup_table()

        self.btn_add.clicked.connect(self.add_storage)
        self.btn_edit.clicked.connect(self.edit_storage)
        self.btn_delete.clicked.connect(self.delete_storage)
        self.tableWidget.itemSelectionChanged.connect(self.load_selected_row)

        self.load_data()

    def setup_combobox(self):
        # Настройка ComboBox для ингредиентов
        self.cb_ingredient.setEditable(True)
        self.cb_ingredient.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.cb_ingredient.completer().setFilterMode(Qt.MatchContains)

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

    def setup_table(self):
        self.tableWidget.setColumnWidth(0, 300)
        self.tableWidget.setColumnWidth(1, 150)
        self.tableWidget.setColumnWidth(2, 150)

    def load_data(self):
        try:
            cursor = self.db_connection.cursor()
            query = """
                SELECT s.storageid, i.ingr_name, s.src_date, s.quantity 
                FROM storages s
                JOIN ingredients i ON s.ingrid = i.ingrid
            """
            cursor.execute(query)
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

        row = selected[0].row()
        try:
            self.selected_id = self.tableWidget.item(row, 0).data(1000)

            # Устанавливаем значения из таблицы
            ingr_name = self.tableWidget.item(row, 0).text()
            date_str = self.tableWidget.item(row, 1).text()
            quantity = self.tableWidget.item(row, 2).text()

            self.cb_ingredient.setCurrentText(ingr_name)
            self.de_date.setDate(QDate.fromString(date_str, "yyyy-MM-dd"))
            self.le_quantity.setText(quantity)

        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка выбора строки: {str(e)}")

    def validate_fields(self):
        try:
            if not self.le_quantity.text().isdigit():
                raise ValueError("Количество должно быть числом")
            if int(self.le_quantity.text()) <= 0:
                raise ValueError("Количество должно быть больше 0")
            if self.cb_ingredient.currentData() is None:
                raise ValueError("Выберите ингредиент")
            return True
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка", str(e))
            return False

    def add_storage(self):
        if not self.validate_fields():
            return

        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                INSERT INTO storages (ingrid, src_date, quantity)
                VALUES (%s, %s, %s)
            """, (
                self.cb_ingredient.currentData(),
                self.de_date.date().toString("yyyy-MM-dd"),
                int(self.le_quantity.text())
            ))
            self.db_connection.commit()
            self.load_data()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка добавления: {str(e)}")

    def edit_storage(self):
        if not self.selected_id:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для редактирования")
            return

        if not self.validate_fields():
            return

        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                UPDATE storages 
                SET ingrid = %s, 
                    src_date = %s, 
                    quantity = %s 
                WHERE storageid = %s
            """, (
                self.cb_ingredient.currentData(),
                self.de_date.date().toString("yyyy-MM-dd"),
                int(self.le_quantity.text()),
                self.selected_id
            ))
            self.db_connection.commit()
            self.load_data()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка редактирования: {str(e)}")

    def delete_storage(self):
        if not self.selected_id:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для удаления")
            return

        try:
            cursor = self.db_connection.cursor()
            cursor.execute("DELETE FROM storages WHERE storageid = %s", (self.selected_id,))
            self.db_connection.commit()
            self.load_data()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка удаления: {str(e)}")
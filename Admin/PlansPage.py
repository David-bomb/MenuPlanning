from header import *


class PlansPage(QDialog):
    def __init__(self, db_connection):
        super().__init__()
        loadUi('UI\PlansPage.ui', self)
        self.db_connection = db_connection
        self.selected_id = None

        self.de_date.setDate(QDate.currentDate())
        self.setup_comboboxes()
        self.setup_table()

        self.btn_add.clicked.connect(self.add_plan)
        self.btn_edit.clicked.connect(self.edit_plan)
        self.btn_delete.clicked.connect(self.delete_plan)
        self.tableWidget.itemSelectionChanged.connect(self.load_selected_row)

        self.load_data()

    def setup_comboboxes(self):
        self.cb_admin.setEditable(True)
        self.cb_admin.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.cb_admin.completer().setFilterMode(Qt.MatchContains)

        self.cb_dish.setEditable(True)
        self.cb_dish.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.cb_dish.completer().setFilterMode(Qt.MatchContains)

        self.load_admins()
        self.load_dishes()

    def load_admins(self):
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT adminid, full_name FROM admins")
            admins = cursor.fetchall()

            self.cb_admin.clear()
            for admin_id, full_name in admins:
                self.cb_admin.addItem(full_name, admin_id)

            cursor.close()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки администраторов: {str(e)}")

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

    def setup_table(self):
        self.tableWidget.setColumnWidth(0, 150)
        self.tableWidget.setColumnWidth(1, 100)
        self.tableWidget.setColumnWidth(2, 250)
        self.tableWidget.setColumnWidth(3, 250)

    def load_data(self):
        try:
            cursor = self.db_connection.cursor()
            query = """
                SELECT p.planid, p.cook_date, p.quantity, 
                       a.full_name, d.dish_name 
                FROM plans p
                JOIN admins a ON p.adminid = a.adminid
                JOIN dishes d ON p.dishid = d.dishid
            """
            cursor.execute(query)
            data = cursor.fetchall()

            self.tableWidget.setRowCount(len(data))
            for row_idx, row_data in enumerate(data):
                self.tableWidget.setItem(row_idx, 0, QTableWidgetItem(str(row_data[1])))
                self.tableWidget.setItem(row_idx, 1, QTableWidgetItem(str(row_data[2])))
                self.tableWidget.setItem(row_idx, 2, QTableWidgetItem(row_data[3]))
                self.tableWidget.setItem(row_idx, 3, QTableWidgetItem(row_data[4]))
                self.tableWidget.item(row_idx, 0).setData(1000, row_data[0])  # Сохраняем ID

            cursor.close()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки планов: {str(e)}")

    def validate_combobox(self, combobox):
        current_text = combobox.currentText()
        for i in range(combobox.count()):
            if combobox.itemText(i) == current_text:
                return True
        QMessageBox.warning(self, "Ошибка", "Неверное значение в выпадающем списке")
        return False

    def add_plan(self):
        try:
            # Валидация полей
            if not self.validate_fields():
                return
            if not self.validate_combobox(self.cb_admin):
                return
            if not self.validate_combobox(self.cb_dish):
                return

            try:
                cursor = self.db_connection.cursor()
                cursor.execute("""
                    INSERT INTO plans (cook_date, quantity, adminid, dishid)
                    VALUES (%s, %s, %s, %s)
                """, (
                    self.de_date.date().toString("yyyy-MM-dd"),
                    int(self.le_quantity.text()),
                    self.cb_admin.currentData(),
                    self.cb_dish.currentData()
                ))
                self.db_connection.commit()
                self.load_data()
            except psycopg2.Error as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка добавления: {str(e)}")
            except Exception as err:
                print(err)
                QMessageBox.critical(self, "Err", str(err))

        except Exception as err:
            print(err)
            QMessageBox.critical(self, "Err", str(err))

    def edit_plan(self):
        if not self.selected_id:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для редактирования")
            return

        if not self.validate_fields():
            return

        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                UPDATE plans 
                SET cook_date = %s, 
                    quantity = %s, 
                    adminid = %s, 
                    dishid = %s 
                WHERE planid = %s
            """, (
                self.de_date.date().toString("yyyy-MM-dd"),
                int(self.le_quantity.text()),
                self.cb_admin.currentData(),
                self.cb_dish.currentData(),
                self.selected_id
            ))
            self.db_connection.commit()
            self.load_data()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка редактирования: {str(e)}")

    def delete_plan(self):
        if not self.selected_id:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для удаления")
            return

        try:
            cursor = self.db_connection.cursor()
            cursor.execute("DELETE FROM plans WHERE planid = %s", (self.selected_id,))
            self.db_connection.commit()
            self.load_data()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка удаления: {str(e)}")
            self.db_connection.rollback()


    def load_selected_row(self):
        selected = self.tableWidget.selectedItems()
        if not selected:
            return

        row = selected[0].row()
        try:
            self.selected_id = self.tableWidget.item(row, 0).data(1000)

            # Дата
            date_str = self.tableWidget.item(row, 0).text()
            self.de_date.setDate(QDate.fromString(date_str, "yyyy-MM-dd"))

            # Количество
            self.le_quantity.setText(self.tableWidget.item(row, 1).text())

            # Администратор и блюдо
            admin_name = self.tableWidget.item(row, 2).text()
            dish_name = self.tableWidget.item(row, 3).text()

            self.cb_admin.setCurrentText(admin_name)
            self.cb_dish.setCurrentText(dish_name)

        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка выбора строки: {str(e)}")

    def validate_fields(self):
        try:
            # Проверка количества
            if not self.le_quantity.text().strip():
                raise ValueError("Поле 'Количество' не может быть пустым")
            if not self.le_quantity.text().isdigit():
                raise ValueError("Количество должно быть числом")
            if int(self.le_quantity.text()) <= 0:
                raise ValueError("Количество должно быть больше нуля")

            # Проверка выбора администратора и блюда
            if self.cb_admin.currentData() is None:
                raise ValueError("Выберите администратора")
            if self.cb_dish.currentData() is None:
                raise ValueError("Выберите блюдо")

            return True

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка", str(e))
            return False
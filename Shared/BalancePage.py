from header import *



class BalancePage(QDialog):
    def __init__(self, db_connection):
        super().__init__()
        loadUi('UI\BalancePage.ui', self)
        self.db_connection = db_connection

        self.setup_comboboxes()
        self.setup_table()

        self.btn_calculate.clicked.connect(self.calculate_balance)
        self.btn_export.clicked.connect(self.handle_export)
        self.btn_close.clicked.connect(self.close)

    def setup_comboboxes(self):
        self.cb_ingredient.setEditable(True)
        self.cb_ingredient.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.cb_ingredient.completer().setFilterMode(Qt.MatchContains)
        self.cb_ingredient.addItem("All", "all")

        self.cb_date.setEditable(True)
        self.cb_date.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.cb_date.completer().setFilterMode(Qt.MatchContains)
        self.cb_date.addItem("All", "all")

        try:
            cursor = self.db_connection.cursor()

            # Загрузка ингредиентов
            cursor.execute("SELECT DISTINCT ingr_name FROM ingredients")
            for (ingr_name,) in cursor.fetchall():
                self.cb_ingredient.addItem(ingr_name, ingr_name)

            # Загрузка дат из планов
            cursor.execute("SELECT DISTINCT cook_date FROM plans ORDER BY cook_date DESC")
            for (date,) in cursor.fetchall():
                self.cb_date.addItem(str(date), str(date))

            cursor.close()
        except psycopg2.Error as e:
            print("Ошибка загрузки фильтров:", e)

    def setup_table(self):
        self.tableWidget.setColumnWidth(0, 300)
        self.tableWidget.setColumnWidth(1, 200)
        self.tableWidget.setColumnWidth(2, 200)
        self.tableWidget.setColumnWidth(3, 200)
        self.tableWidget.setEditTriggers(QTableWidget.NoEditTriggers)

    def calculate_balance(self):
        try:
            date_filter = self.cb_date.currentData() if self.cb_date.currentData() else "all"
            ingredient_filter = self.cb_ingredient.currentData() if self.cb_ingredient.currentData() else "all"

            try:
                cursor = self.db_connection.cursor()

                query = """
                    SELECT 
                        i.ingr_name,
                        SUM(p.quantity * c.quantity) AS required,
                        COALESCE(SUM(s.quantity), 0) AS in_stock,
                        (COALESCE(SUM(s.quantity), 0) - SUM(p.quantity * c.quantity)) AS balance
                    FROM plans p
                    JOIN cooking c ON p.dishid = c.dishid
                    JOIN ingredients i ON c.ingrid = i.ingrid
                    LEFT JOIN storages s ON i.ingrid = s.ingrid
                    WHERE 
                        (%s = 'all' OR p.cook_date::text = %s) AND
                        (%s = 'all' OR i.ingr_name = %s)
                    GROUP BY i.ingr_name
                """

                cursor.execute(query, (
                    date_filter, date_filter,
                    ingredient_filter, ingredient_filter
                ))

                data = cursor.fetchall()

                self.tableWidget.setRowCount(len(data))
                for row_idx, row_data in enumerate(data):
                    self.tableWidget.setItem(row_idx, 0, QTableWidgetItem(row_data[0]))
                    self.tableWidget.setItem(row_idx, 1, QTableWidgetItem(str(row_data[1])))
                    self.tableWidget.setItem(row_idx, 2, QTableWidgetItem(str(row_data[2])))

                    balance_item = QTableWidgetItem(str(row_data[3]))
                    if row_data[3] < 0:
                        balance_item.setBackground(QColor(255, 200, 200))
                    else:
                        balance_item.setBackground(QColor(200, 255, 200))
                    self.tableWidget.setItem(row_idx, 3, balance_item)

                cursor.close()
            except psycopg2.Error as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка расчета баланса: {str(e)}")
        except Exception as e:
            print(e)

    def handle_export(self):
        path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Экспорт данных",
            "",
            "PDF Files (*.pdf);;CSV Files (*.csv);;JSON Files (*.json)"
        )

        if not path:
            return

        if selected_filter == "PDF Files (*.pdf)":
            self.export_pdf(path)
        elif selected_filter == "CSV Files (*.csv)":
            self.export_csv(path)
        elif selected_filter == "JSON Files (*.json)":
            self.export_json(path)

    def export_pdf(self, path):
        try:
            try:
                pdfmetrics.registerFont(TTFont('DejaVuSans', '../static/fonts/DejaVuSans.ttf'))
                font_name = 'DejaVuSans'
            except Exception as font_error:
                QMessageBox.warning(self, "Ошибка", f"Шрифт не загружен: {str(font_error)}")
                font_name = 'Helvetica'

            if self.tableWidget.rowCount() == 0:
                QMessageBox.warning(self, "Ошибка", "Нет данных для экспорта!")
                return

            data = []
            styles = getSampleStyleSheet()

            headers = [
                Paragraph(f'<font name="{font_name}">Ингредиент</font>', styles['Normal']),
                Paragraph(f'<font name="{font_name}">Требуется</font>', styles['Normal']),
                Paragraph(f'<font name="{font_name}">На складе</font>', styles['Normal']),
                Paragraph(f'<font name="{font_name}">Баланс</font>', styles['Normal'])
            ]
            data.append(headers)

            for row in range(self.tableWidget.rowCount()):
                row_data = []
                for col in range(4):
                    item = self.tableWidget.item(row, col)
                    text = item.text() if item and item.text() else ""
                    row_data.append(text)

                data.append([
                    Paragraph(f'<font name="{font_name}">{cell}</font>', styles['Normal'])
                    for cell in row_data
                ])

            doc = SimpleDocTemplate(
                path,
                pagesize=A4,
                rightMargin=1 * cm,
                leftMargin=1 * cm,
                topMargin=2 * cm,
                bottomMargin=2 * cm
            )

            col_widths = [
                (A4[0] - 2 * cm) * 0.4,
                (A4[0] - 2 * cm) * 0.2,
                (A4[0] - 2 * cm) * 0.2,
                (A4[0] - 2 * cm) * 0.2
            ]

            table = Table(data, colWidths=col_widths, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), font_name),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
            ]))

            elements = [Spacer(1, 1 * cm), table]
            doc.build(elements)
            QMessageBox.information(self, "Успех", "PDF успешно экспортирован!")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка экспорта PDF: {str(e)}")

    def export_csv(self, path):
        try:
            if self.tableWidget.rowCount() == 0:
                QMessageBox.warning(self, "Ошибка", "Нет данных для экспорта!")
                return

            with open(path, 'w', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file, delimiter=';')
                writer.writerow(['Ингредиент', 'Требуется', 'На складе', 'Баланс'])

                for row in range(self.tableWidget.rowCount()):
                    row_data = [
                        self.tableWidget.item(row, col).text() if self.tableWidget.item(row, col) else ""
                        for col in range(4)
                    ]
                    writer.writerow(row_data)

            QMessageBox.information(self, "Успех", "CSV успешно экспортирован!")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка экспорта CSV: {str(e)}")

    def export_json(self, path):
        try:
            if self.tableWidget.rowCount() == 0:
                QMessageBox.warning(self, "Ошибка", "Нет данных для экспорта!")
                return

            data = []
            for row in range(self.tableWidget.rowCount()):
                item = {
                    "ingredient": self.tableWidget.item(row, 0).text() if self.tableWidget.item(row, 0) else "",
                    "required": self.tableWidget.item(row, 1).text() if self.tableWidget.item(row, 1) else "",
                    "in_stock": self.tableWidget.item(row, 2).text() if self.tableWidget.item(row, 2) else "",
                    "balance": self.tableWidget.item(row, 3).text() if self.tableWidget.item(row, 3) else ""
                }
                data.append(item)

            with open(path, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)

            QMessageBox.information(self, "Успех", "JSON успешно экспортирован!")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка экспорта JSON: {str(e)}")
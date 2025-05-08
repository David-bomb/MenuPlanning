import sys
from PyQt5.QtWidgets import QDialog, QMessageBox, QApplication, QTableWidgetItem, QCompleter, QFileDialog, QTableWidget
from PyQt5.uic import loadUi
import psycopg2
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
import csv
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QLineEdit, QMessageBox, QHBoxLayout
from PyQt5.QtChart import QChart, QChartView, QPieSeries
import sys


class InputDisplayApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Input Display App")
        self.setGeometry(100, 100, 300, 200)

        self.layout = QVBoxLayout()

        self.label = QLabel("Enter something:")
        self.layout.addWidget(self.label)

        self.entry = QLineEdit()
        self.layout.addWidget(self.entry)

        self.button = QPushButton("Submit")
        self.button.clicked.connect(self.process_input)
        self.layout.addWidget(self.button)

        self.setLayout(self.layout)

    def process_input(self):
        user_input = self.entry.text()
        if user_input:
            self.expense_window = ExpenseReport()
            self.expense_window.show()
            self.close()
        else:
            QMessageBox.warning(self, "Input Error", "Please enter a value")


class ExpenseReport(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Expense and Earnings Report")
        self.setGeometry(100, 100, 600, 400)

        layout = QHBoxLayout()

        data_layout = QVBoxLayout()
        self.expense_label = QLabel("Expenses: $2000")
        self.earning_label = QLabel("Earnings: $5000")
        self.dti_label = QLabel("Debt-to-Income Ratio: 40%")

        data_layout.addWidget(self.expense_label)
        data_layout.addWidget(self.earning_label)
        data_layout.addWidget(self.dti_label)

        layout.addLayout(data_layout)

        # Creating a Pie Chart
        self.series = QPieSeries()
        self.series.append("Expenses", 2000)
        self.series.append("Earnings", 5000)

        self.chart = QChart()
        self.chart.addSeries(self.series)
        self.chart.setTitle("Monthly Financial Overview")

        self.chart_view = QChartView(self.chart)
        layout.addWidget(self.chart_view)

        self.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InputDisplayApp()
    window.show()
    sys.exit(app.exec_())

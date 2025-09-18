import base64
import datetime
import sys
from os import listdir
from os.path import isfile, join

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QColor
from cryptography import x509
from cryptography.hazmat.backends import default_backend

import yaml
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDesktopWidget,
    QPushButton,
    QFileDialog, QMessageBox,
)


class NumericTableWidgetItem(QTableWidgetItem):
    def __lt__(self, other: object):
        try:
            return int(self.text()) < int(other.text())
        except (ValueError, TypeError):
            return super().__lt__(other)


class App(QWidget):
    def __init__(self):
        super().__init__()

        self.directory: str | None = None
        self.warning_days: int = 10

        self.setWindowTitle('Certificate Viewer')
        self.setMinimumSize(QSize(900, 500))
        self.center_window()

        self.layout = QVBoxLayout()

        self.select_folder_button = QPushButton('Select Folder')
        self.select_folder_button.clicked.connect(self.select_directory)
        self.layout.addWidget(self.select_folder_button)

        self.table = self.create_table()
        self.layout.addWidget(self.table)
        self.setLayout(self.layout)

        self.parse_arguments(app.arguments())

        if self.directory:
            self.load_data(self.table)

        self.show()

    def parse_arguments(self, args: list[str]):
        if len(args) > 1:
            for arg in args:
                if arg.startswith('--path=', 0, 7):
                    self.directory = str(arg.split('--path=')[1])
                elif arg.startswith('--days=', 0, 7):
                    self.warning_days = int(arg.split('--days=')[1])

    def center_window(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def select_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, 'Select Folder', self.directory)
        if dir_path:
            self.directory = dir_path
            self.update_table()

    def create_table(self) -> QTableWidget:
        tableWidget = QTableWidget()
        tableWidget.setColumnCount(5)
        tableWidget.setColumnWidth(0, 300)
        tableWidget.setColumnWidth(1, 170)
        tableWidget.setColumnWidth(2, 140)
        tableWidget.setColumnWidth(3, 140)
        tableWidget.setColumnWidth(4, 110)

        tableWidget.setSortingEnabled(True)
        tableWidget.setHorizontalHeaderLabels(['File', 'Cluster', 'Start Data', 'Expire Data', 'Days to expire'])
        tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        tableWidget.horizontalHeader().setStretchLastSection(True)

        return tableWidget

    def load_data(self, table: QTableWidget) -> None:
        rows = []
        for file in [f for f in listdir(self.directory) if isfile(join(self.directory, f))]:
            try:
                data = self.read_yaml_file(join(self.directory, file))
                if not isinstance(data, dict):
                    continue

                client_certificate_data_base64 = data['users'][0]['user']['client-certificate-data']
                cluster_name = data.get('clusters', [{}])[0].get('name', '')

                if client_certificate_data_base64:
                    pem_data = base64.b64decode(client_certificate_data_base64)
                    cert = x509.load_pem_x509_certificate(pem_data, default_backend())

                    rows.append(
                        [
                            file,
                            cluster_name,
                            cert.not_valid_before_utc.date(),
                            cert.not_valid_after_utc.date(),
                            (cert.not_valid_after_utc.date() - datetime.date.today()).days,
                        ]
                    )
            except (KeyError, TypeError, ValueError):
                continue

        table.setRowCount(len(rows))
        row_color = QColor(255, 0, 0)
        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                if j == 4:
                    item = NumericTableWidgetItem(str(value))
                else:
                    item = QTableWidgetItem(str(value))
                if row[-1] <= self.warning_days:
                    item.setBackground(row_color)
                table.setItem(i, j, item)

        if not rows:
            QMessageBox.information(
                self,
                'Information',
                'No valid Kubernetes config files found in the selected directory.',
            )

        table.resizeRowsToContents()
        table.sortByColumn(4, Qt.AscendingOrder)

    def update_table(self) -> None:
        self.table.clearContents()
        self.load_data(self.table)

    def read_yaml_file(self, filename: str) -> dict:
        with open(filename, 'r') as f:
            return yaml.safe_load(f)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())

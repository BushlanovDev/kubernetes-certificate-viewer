import base64
import datetime
import sys
from os import listdir
from os.path import isfile, join

from PyQt5.QtCore import QSize
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
    QFileDialog,
)


class App(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Certificate Viewer')
        self.setMinimumSize(QSize(900, 500))
        self.center_window()

        self.directory: str | None = None

        self.layout = QVBoxLayout()

        self.select_folder_button = QPushButton('Select Folder')
        self.select_folder_button.clicked.connect(self.select_directory)
        self.layout.addWidget(self.select_folder_button)

        self.table = self.create_table()
        self.layout.addWidget(self.table)

        self.setLayout(self.layout)
        self.show()

        self.parse_arguments(app.arguments())

    def parse_arguments(self, args: list[str]):
        if len(args) > 1:
            for arg in args:
                if arg.startswith('--path=', 0, 7):
                    self.directory = str(arg.split('--path=')[1])
                    self.load_data(self.table)

    def center_window(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def select_directory(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, 'Select Folder', self.directory
        )
        if dir_path:
            self.directory = dir_path
            self.update_table()

    def create_table(self) -> QTableWidget:
        tableWidget = QTableWidget()
        tableWidget.setColumnCount(5)
        tableWidget.setColumnWidth(0, 300)
        tableWidget.setColumnWidth(1, 140)
        tableWidget.setColumnWidth(2, 140)
        tableWidget.setColumnWidth(3, 140)
        tableWidget.setColumnWidth(4, 140)

        tableWidget.setHorizontalHeaderLabels(
            ['File', 'Cluster', 'Start Data', 'Expire Data', 'Days to expire']
        )
        tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        tableWidget.horizontalHeader().setStretchLastSection(True)

        return tableWidget

    def load_data(self, table: QTableWidget) -> None:
        rows = []
        for file in [
            f for f in listdir(self.directory) if isfile(join(self.directory, f))
        ]:
            data = self.read_yaml_file(join(self.directory, file))
            if isinstance(data, dict):
                try:
                    client_certificate_data_base64 = data['users'][0]['user'][
                        'client-certificate-data'
                    ]
                except KeyError:
                    continue

                try:
                    cluster_name = data['clusters'][0]['name']
                except KeyError:
                    cluster_name = ''

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

        table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                table.setItem(i, j, QTableWidgetItem(str(value)))

        table.resizeRowsToContents()

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

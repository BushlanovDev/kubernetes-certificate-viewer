import base64
import datetime
import sys
from os import listdir
from os.path import isfile, join
from typing import Any

from PyQt5.QtCore import QSize, Qt, QUrl
from PyQt5.QtGui import QColor, QIcon, QDesktopServices
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
    QMessageBox,
    QMenu,
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

        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

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
        tableWidget.setColumnWidth(1, 180)
        tableWidget.setColumnWidth(2, 130)
        tableWidget.setColumnWidth(3, 130)
        tableWidget.setColumnWidth(4, 90)

        tableWidget.setSortingEnabled(True)
        tableWidget.setHorizontalHeaderLabels(['File', 'Cluster', 'Start Data', 'Expire Data', 'Days to expire'])
        tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        tableWidget.horizontalHeader().setStretchLastSection(True)

        return tableWidget

    def load_data(self, table: QTableWidget) -> None:
        rows = []
        if not self.directory or not isdir(self.directory):
            QMessageBox.warning(self, 'Warning', 'The specified directory does not exist.')
            return

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
                            cert.not_valid_before_utc.date().strftime('%Y.%m.%d'),
                            cert.not_valid_after_utc.date().strftime('%Y.%m.%d'),
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

                if j == 0:
                    full_path = join(self.directory, str(value))
                    item.setToolTip(full_path)

                if j in [2, 3, 4]:
                    item.setTextAlignment(Qt.AlignCenter)

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

    def read_yaml_file(self, filename: str) -> dict | None:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except (yaml.YAMLError, UnicodeDecodeError):
            return None

    def show_context_menu(self, pos: Any):
        item = self.table.itemAt(pos)
        if item is None:
            return

        context_menu = QMenu(self)
        view_action = context_menu.addAction("View")

        action = context_menu.exec_(self.table.mapToGlobal(pos))
        if action == view_action:
            self.view_row_details(item.row())

    def view_row_details(self, row_index: int):
        file = self.table.item(row_index, 0).text()
        cluster = self.table.item(row_index, 1).text()
        start_date = self.table.item(row_index, 2).text()
        expire_date = self.table.item(row_index, 3).text()

        details_text = (
            f"<b>File:</b> {file}<br>"
            f"<b>Cluster:</b> {cluster}<br>"
            f"<b>Start Date:</b> {start_date}<br>"
            f"<b>Expire Data:</b> {expire_date}"
        )

        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setWindowTitle("Certificate Details")
        msg_box.setText(details_text)

        open_button = msg_box.addButton("Open File", QMessageBox.ActionRole)
        msg_box.addButton("Close", QMessageBox.RejectRole)

        msg_box.exec_()

        if msg_box.clickedButton() == open_button:
            if self.directory:
                full_path = join(self.directory, file)
                QDesktopServices.openUrl(QUrl.fromLocalFile(full_path))


if __name__ == '__main__':
    from os.path import isdir

    app = QApplication(sys.argv)
    try:
        app.setWindowIcon(QIcon('resources/icon32.ico'))
    except FileNotFoundError:
        print("Icon not found, proceeding without it.")
    ex = App()
    sys.exit(app.exec_())

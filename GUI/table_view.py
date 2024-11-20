from datetime import datetime
from Models.data_view import DataView
from PyQt6.QtWidgets import QTableWidgetItem
from GUI.Tools.tablewidget_with_copy import TableWidgetWithCopy


class TableView:

    def __init__(self, tablewidget_with_copy: TableWidgetWithCopy):
        self.tablewidget_with_copy: TableWidgetWithCopy = tablewidget_with_copy

    def show_data(self, data_view: DataView):
        assert len(data_view.get_data_stores()) == 1
        for data_store in data_view.get_data_stores():
            self.tablewidget_with_copy.setColumnCount(len(data_store.data))
            for col, data_item in enumerate(data_store.data):
                header_item = QTableWidgetItem(data_item)
                font = header_item.font()
                font.setBold(True)
                header_item.setFont(font)
                self.tablewidget_with_copy.setHorizontalHeaderItem(col, header_item)
            lengths = [len(values) for values in data_store.data.values()]
            assert all([length == lengths[0] for length in lengths])
            self.tablewidget_with_copy.setRowCount(lengths[0])
            for col, data_item in enumerate(data_store.data):
                for row, value in enumerate(data_store.data[data_item]):
                    value_repr = datetime.fromtimestamp(value) if data_item == 'timestamp' else str(value)
                    self.tablewidget_with_copy.setItem(row, col, QTableWidgetItem(str(value_repr)))
        self.tablewidget_with_copy.resizeColumnsToContents()

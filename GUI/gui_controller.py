from GUI.gui_view import GUIView
from ServerRequests.server_requests import ServerRequests


class GUIController:
    """ Controller voor het main screen """

    def __init__(self):
        self.view = GUIView()
        self.view.connectEvents(
            {
                'nuSelected': self.nuSelected,
                'fromChanged': self.fromChanged,
                'toChanged': self.toChanged,
            }
        )
        self.data = None
        self.view.show()

    def nuSelected(self):
        print("nuSelected")
        self.data = ServerRequests().get_data()
        self.view.initTimeFrame()
        self.view.show_data(self.data)

    def fromChanged(self):
        self.view.show_data(self.data)

    def toChanged(self):
        self.view.show_data(self.data)


from GUI.gui_view import GUIView
from GUI.gui_model import GUIModel


class GUIController:
    """ Controller voor het main screen """

    def __init__(self):
        self.view = GUIView(self.time_range_changed_CB)
        self.model = GUIModel(self.view)
        self.view.connectEvents(
            {
                'nuSelected': self.nuSelected,
                'dagenSelected': self.dagenSelected,
                'timeRangeChanged': self.timeRangeChanged,
            }
        )
        self.view.show()

    def time_range_changed_CB(self, time_range):
        self.model.set_time_range(time_range)

    def nuSelected(self):
        print("nuSelected")
        self.model.acquire_data('realtime')
#        self.update_to_time()

    def dagenSelected(self):
        print("dagenSelected")
        self.model.acquire_data('persistent')
        self.view.show_data(self.model.get_data(), self.model.get_time_range())

    def timeRangeChanged(self):
        time_range = self.view.get_time_range()
        self.model.set_time_range(time_range)


from sys import argv, exit
from PyQt5.QtWidgets import QApplication

from tools.utils import goto
from tools.utils_gui import npcap_exists, duplicate_elmocut, repair_settings
from tools.qtools import msg_box, Buttons, MsgIcon

from gui.main import ElmoCut

from assets import app_icon
from constants import *

if __name__ == "__main__":
    app = QApplication(argv)
    icon = ElmoCut.processIcon(app_icon)

    # Check if Npcap is installed
    if not npcap_exists():
        if msg_box('elmoCut', 'Npcap is not installed\n\nClick OK to download',
                    MsgIcon.CRITICAL, icon, Buttons.OK | Buttons.CANCEL) == Buttons.OK:
            goto(NPCAP_URL)
    
    # Check if another elmoCut process is running
    elif duplicate_elmocut():
        msg_box('elmoCut', 'elmoCut is already running!', MsgIcon.WARN, icon)
    
    # Run the GUI
    else:
        repair_settings()
        GUI = ElmoCut()
        GUI.show()
        GUI.resizeEvent()
        GUI.scanner.init()
        GUI.scanner.flush_arp()
        GUI.scanEasy()
        GUI.UpdateThread_Starter()
        exit(app.exec_())
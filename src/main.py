from qdarkstyle import load_stylesheet
from pyperclip import copy

from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QMessageBox, \
                            QMenu, QSystemTrayIcon, QAction
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt

from ui_main import Ui_MainWindow
from settings import Settings
from qtools import colored_item

from scanner import Scanner
from killer import Killer

from assets import app_icon, \
                   kill_icon, killall_icon, \
                   unkill_icon, unkillall_icon, \
                   scan_easy_icon, scan_hard_icon, \
                   settings_icon, about_icon

from utils_gui import update_settings, get_settings
from utils import is_connected

from connector import ScanThread

CONNECTED = True

def check_connection(func):
    """
    Connection checker decorator
    """
    def wrapper(*args, **kargs):
        # for def func(self): in class
        # will return kargs = {}
        # and return args = (<__main__.ElmoCut object at 0x00000....etc>, False)
        # so we chose the "self" reference: args[0] = <__main__.ElmoCut object at 0x00000....etc>
        if CONNECTED:
            return func(args[0])
    return wrapper

class ElmoCut(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.version = 0.2
        icon = self.processIcon(app_icon)

        # Add window icon
        self.setWindowIcon(icon)
        self.setupUi(self)
        self.setStyleSheet(load_stylesheet())
        
        # Main Props
        self.scanner = Scanner()
        self.killer = Killer()
        self.minimize = True
        self.remember = False
        self.from_tray = False
        
        # We send elmocut to the settings window
        self.settings_window = Settings(self, icon)

        self.applySettings()

        # Threading
        self.scan_thread = ScanThread()
        self.scan_thread.thread_finished.connect(self.ScanThread_Reciever)
        self.scan_thread.progress.connect(self.pgbar.setValue)
        
        # Connect buttons
        self.buttons = [
            (self.btnScanEasy,  self.scanEasy,     scan_easy_icon, 'Arping Scan'),
            (self.btnScanHard,  self.scanHard,     scan_hard_icon, 'Pinging Scan'),
            (self.btnKill,      self.kill,         kill_icon,      'Kill selected device'),
            (self.btnUnkill,    self.unkill,       unkill_icon,    'Un-kill selected device'),
            (self.btnKillAll,   self.killAll,      killall_icon,   'Kill all devices'),
            (self.btnUnkillAll, self.unkillAll,    unkillall_icon, 'Un-kill all devices'),
            (self.btnSettings,  self.openSettings, settings_icon,  'View elmoCut settings'),
            (self.btnAbout,     self.openAbout,    about_icon,     'About elmoCut')
            ]
        
        for btn, btn_func, btn_icon, btn_tip in self.buttons:
            btn.clicked.connect(btn_func)
            btn.setIcon(
                self.processIcon(btn_icon)
            )
            btn.setToolTip(btn_tip)

        self.pgbar.setVisible(False)

        # Table Widget
        self.tableScan.itemClicked.connect(self.deviceClicked)
        self.tableScan.cellClicked.connect(self.cellClicked)
        self.tableScan.setColumnCount(4)
        self.tableScan.verticalHeader().setVisible(False)
        self.tableScan.setHorizontalHeaderLabels(['IP Address','MAC Address','Vendor','Type'])

        '''
           System tray icon and it's tray menu
        '''
        show_option = QAction('Show', self)
        hide_option = QAction('Hide', self)
        quit_option = QAction('Quit', self)
        kill_option = QAction(self.processIcon(kill_icon), '&Kill All', self)
        unkill_option = QAction(self.processIcon(unkill_icon),'&Unkill All', self)
        
        show_option.triggered.connect(self.show)
        hide_option.triggered.connect(self.hide_all)
        quit_option.triggered.connect(self.quit_all)
        kill_option.triggered.connect(self.killAll)
        unkill_option.triggered.connect(self.unkillAll)
        
        tray_menu = QMenu()
        tray_menu.addAction(show_option)
        tray_menu.addAction(hide_option)
        tray_menu.addSeparator()
        tray_menu.addAction(kill_option)
        tray_menu.addAction(unkill_option)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_option)
        
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip('elmoCut')
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.tray_clicked)
    
    @staticmethod
    def processIcon(icon_data):
        """
        Create icon pixmap object from raw data
        """
        pix = QPixmap()
        icon = QIcon()
        pix.loadFromData(icon_data)
        icon.addPixmap(pix)
        return icon

    def applySettings(self):
        """
        Apply saved settings
        """
        self.settings_window.updateElmocutSettings()

    def openSettings(self):
        """
        Open settings window
        """
        self.settings_window.currentSettings()
        self.settings_window.show()
    
    def openAbout(self):
        """
        Open about window
        """
        QMessageBox.information(self, 'About', 'Built with love by:\n\nKhaled El-Morshedy')

    def tray_clicked(self, event):
        """
        Show elmoCut when tray icon is left-clicked
        """
        if event == QSystemTrayIcon.Trigger:
            self.show()

    def hide_all(self):
        """
        Hide option for tray (Hides window and settings)
        """
        self.hide()
        self.settings_window.hide()

    def quit_all(self):
        """
        Unkill any killed device on exit from tray icon
        """
        self.killer.unkill_all()
        self.settings_window.close()
        self.from_tray = True
        self.close()

    def resizeEvent(self, event=True):
        """
        Auto resize table widget columns dynamically
        """
        for i in range(4):
            self.tableScan.setColumnWidth(i, self.tableScan.width() // 4)

    def closeEvent(self, event):
        """
        Run in background if self.minimize is True else exit
        """
        # If event recieved from tray icon
        if self.from_tray:
            event.accept()
            return
        
        # If event is recieved from close X button
        
        ## If minimize is true
        if self.minimize:
            event.ignore()
            self.hide_all()
            return
        
        ## If not kill all and shutdown
        self.killer.unkill_all()
        self.settings_window.close()
        event.accept()

        QMessageBox.information(
            self,
            'Shutdown',
            'elmoCut will exit completely.\n\n'
            'Enable minimized from settings\nto'
            ' be able to run in background.'
        )
    
    def log(self, text, color='white'):
        """
        Print log info at left label
        """
        self.lblleft.setText(f"<font color='{color}'>{text}</font>")
    
    def connected(self):
        """
        Check for Internet connection
        """
        globals()['CONNECTED'] = True

        if not is_connected():
            self.log('No Internet Connection', 'red')
            self.pgbar.setVisible(False)

            globals()['CONNECTED'] = False
        
        return CONNECTED

    def current_index(self):
        return self.scanner.devices[self.tableScan.currentRow()]
    
    def cellClicked(self, row, column):
        """
        Copy selected cell data to clipboard
        """
        # Get current row
        device = self.current_index()

        # Get cell text using dict.values instead of .itemAt()
        cell = list(device.values())[column]
        self.lblcenter.setText(cell)
        copy(cell)

    def deviceClicked(self):
        """
        Disable kill, unkill buttons when admins are selected
        """
        not_enabled = not self.current_index()['admin']
        
        self.btnKill.setEnabled(not_enabled)
        self.btnUnkill.setEnabled(not_enabled)
    
    def showDevices(self):
        """
        View scanlist devices with correct colors processed
        """
        self.tableScan.clearSelection()
        self.tableScan.clearContents()
        self.tableScan.setRowCount(len(self.scanner.devices))

        for row, device in enumerate(self.scanner.devices):
            for column, item in enumerate(device.values()):
                # Skip 'admin' key
                if type(item) == bool:
                    continue
                
                # Center text in eah cell
                ql = QTableWidgetItem()
                ql.setText(item)
                ql.setTextAlignment(Qt.AlignCenter)
                
                # Highlight Admins and killed devices
                if device['admin']:
                    colored_item(ql, '#00ff00', '#000000')
                if device['mac'] in self.killer.killed:
                    colored_item(ql, '#ff0000', '#ffffff')
                
                # Add cell to the row
                self.tableScan.setItem(row, column, ql)
        
        self.lblright.setText(
                            f'{len(self.scanner.devices) - 1} devices'
                            f' ({len(self.killer.killed)} killed)'
        )
        
        # Show selected cell data
        self.lblcenter.setText('Nothing Selected')

    @check_connection
    def kill(self):
        """
        Apply ARP spoofing to selected device
        """
        if not self.tableScan.selectedItems():
            self.log('No device selected.', 'red')
            return

        device = self.current_index()
        
        if device['mac'] in self.killer.killed:
            self.log('Device is already killed.', 'red')
            return
        
        # Killing process
        self.killer.kill(device)
        update_settings('killed', list(self.killer.killed) * self.remember)
        self.log('Killed ' + device['ip'], 'fuchsia')
        
        self.showDevices()
    
    @check_connection
    def unkill(self):
        """
        Disable ARP spoofing on previously spoofed devices
        """
        if not self.tableScan.selectedItems():
            self.log('No device selected.', 'red')
            return

        device = self.current_index()
            
        if device['mac'] not in self.killer.killed:
            self.log('Device is already unkilled.', 'red')
            return
        
        # Unkilling process
        self.killer.unkill(device)
        update_settings('killed', list(self.killer.killed) * self.remember)
        self.log('Unkilled ' + device['ip'], 'lime')

        self.showDevices()
    
    @check_connection
    def killAll(self):
        """
        Kill all scanned devices except admins
        """
        self.killer.kill_all(self.scanner.devices)
        update_settings('killed', list(self.killer.killed) * self.remember)
        self.log('Killed All devices.', 'fuchsia')

        self.showDevices()

    @check_connection
    def unkillAll(self):
        """
        Unkill all killed devices except admins
        """
        self.killer.unkill_all()
        update_settings('killed', list(self.killer.killed) * self.remember)
        self.log('Unkilled All devices.', 'lime')

        self.showDevices()

    def processDevices(self):
        """
        Rekill any paused device after scan
        """
        self.tableScan.clearSelection()
        
        # first device in list is the router
        self.killer.router = self.scanner.router

        # re-kill paused and update to current devices
        self.killer.rekill_stored(self.scanner.devices)
        for rem_device in self.scanner.devices:
            if rem_device['mac'] in get_settings('killed'):
                self.killer.kill(rem_device)

        # clear old database
        self.killer.release()

        self.log(
            f'Found {len(self.scanner.devices) - 1} devices.',
            'orange'
        )

        self.showDevices()
    
    def scanEasy(self):
        """
        Easy Scan button connector
        """
        self.ScanThread_Starter()
    
    def scanHard(self):
        """
        Hard Scan button connector
        """
        # Set correct max for progress bar
        self.ScanThread_Starter(scan_type=1)
    
    def ScanThread_Starter(self, scan_type=0):
        """
        self.scan_thread QThread Starter
        """
        if not self.connected():
            return
        
        self.centralwidget.setEnabled(False)
        
        # Save copy of killed devices
        self.killer.store()
        
        self.killer.unkill_all()
        
        self.log(
            ['Arping', 'Pinging'][scan_type] + ' your network...',
            ['aqua', 'fuchsia'][scan_type]
        )
        
        self.pgbar.setVisible(True)
        self.pgbar.setMaximum(self.scanner.device_count)
        self.pgbar.setValue(self.scanner.device_count * (not scan_type))
        
        self.scan_thread.scanner = self.scanner
        self.scan_thread.scan_type = scan_type
        self.scan_thread.start()

    def ScanThread_Reciever(self):
        """
        self.scan_thread QThread results reciever
        """
        self.centralwidget.setEnabled(True)
        self.pgbar.setVisible(False)
        self.processDevices()
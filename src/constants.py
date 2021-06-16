NPCAP_URL = 'https://nmap.org/npcap/dist/npcap-1.10.exe'

NPCAP_PATH = 'C:\\Windows\\SysWOW64\\Npcap'

GLOBAL_MAC = 'FF:FF:FF:FF:FF:FF'

DUMMY_ROUTER = {
    'ip': '192.168.1.1',
    'mac': 'FF:FF:FF:FF:FF:FF',
    'vendor': 'NONE',
    'type': 'Router',
    'admin': True
}

DUMMY_IFACE = {'name': 'NULL', 'mac': GLOBAL_MAC, 'guid': 'NULL', 'ips': ['0.0.0.0']}

HKEY_AUTOSTART_PATH = 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run'

SETTINGS_KEYS = ['dark', 'count', 'autostart', 'minimized', 'remember', 'killed', 'autoupdate', 'threads', 'iface']

SETTINGS_VALS = [True, 25, False, True, False, [], True, 12, '']
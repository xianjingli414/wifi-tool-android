from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
import sqlite3
import os

class WiFiToolApp(App):
    def build(self):
        self.db_path = os.path.join(self.user_data_dir, 'wifi_data.db')
        self.init_db()
        
        self.title = 'WiFi采集管理工具'
        
        # 主布局
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 标题
        title = Label(
            text='WiFi 采集管理工具',
            size_hint_y=None,
            height='50dp',
            font_size='20sp'
        )
        main_layout.add_widget(title)
        
        # 扫描按钮
        scan_btn = Button(
            text='扫描 WiFi',
            size_hint_y=None,
            height='50dp',
            background_color=(0.2, 0.7, 0.3, 1)
        )
        scan_btn.bind(on_press=self.scan_wifi)
        main_layout.add_widget(scan_btn)
        
        # WiFi 列表
        self.wifi_list = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.wifi_list.bind(minimum_height=self.wifi_list.setter('height'))
        
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(self.wifi_list)
        main_layout.add_widget(scroll)
        
        # 状态栏
        self.status = Label(
            text='就绪',
            size_hint_y=None,
            height='30dp'
        )
        main_layout.add_widget(self.status)
        
        return main_layout
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wifi_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ssid TEXT,
                bssid TEXT,
                signal_strength INTEGER,
                security_type TEXT,
                frequency TEXT,
                scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def scan_wifi(self, instance):
        self.status.text = '扫描中...'
        # 模拟扫描结果（Android 版本需要用 pyjnius 调用 WifiManager）
        import random
        mock_results = [
            {'ssid': f'WiFi_{i}', 'bssid': f'00:11:22:33:44:{i:02x}', 'signal': random.randint(-80, -30)}
            for i in range(5)
        ]
        self.show_results(mock_results)
        self.status.text = f'找到 {len(mock_results)} 个网络'
    
    def show_results(self, results):
        self.wifi_list.clear_widgets()
        for wifi in results:
            item = BoxLayout(orientation='horizontal', size_hint_y=None, height='40dp')
            item.add_widget(Label(text=wifi['ssid'], size_hint_x=0.4))
            item.add_widget(Label(text=f\"{wifi['signal']} dBm\", size_hint_x=0.3))
            item.add_widget(Label(text=wifi['bssid'], size_hint_x=0.3))
            self.wifi_list.add_widget(item)

if __name__ == '__main__':
    WiFiToolApp().run()

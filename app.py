# -*- coding: utf-8 -*-
"""
app.py - Kivy 主应用（纯 Kivy，无 KivyMD 依赖）
三页布局：扫描 / 历史 / 管理，底部按钮导航
"""

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.properties import StringProperty, ListProperty, ObjectProperty, BooleanProperty
from kivy.uix.widget import Widget
from kivy.uix.togglebutton import ToggleButton
from kivy.graphics import Color, Rectangle

import sys
import os
import datetime
import threading
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database
import wifi_scanner
import export_utils

# ═════════════════════════════════════════════════════════
# 颜色常量
# ═════════════════════════════════════════════════════════

COLOR_PRIMARY   = (0.18, 0.46, 0.71, 1)   # #2F75B6
COLOR_PRIMARY_L = (0.24, 0.55, 0.82, 1)
COLOR_DANGER   = (0.88, 0.22, 0.22, 1)
COLOR_SUCCESS   = (0.18, 0.68, 0.32, 1)
COLOR_GRAY     = (0.60, 0.60, 0.60, 1)
COLOR_BG       = (0.96, 0.96, 0.96, 1)
COLOR_WHITE    = (1, 1, 1, 1)
COLOR_TEXT     = (0.15, 0.15, 0.15, 1)
COLOR_TEXT_L   = (0.45, 0.45, 0.45, 1)


# ═════════════════════════════════════════════════════════
# 通用辅助
# ═════════════════════════════════════════════════════════

def ts():
    return datetime.datetime.now().strftime("%H:%M:%S")

def make_btn(text, on_press=None, size_hint_x=1, bg=COLOR_PRIMARY):
    """创建统一样式的按钮"""
    b = Button(
        text=text,
        size_hint_y=None, height=40,
        size_hint_x=size_hint_x,
        background_normal="",
        background_color=bg,
        color=COLOR_WHITE,
        font_size="14sp",
    )
    if on_press:
        b.bind(on_press=on_press)
    return b

def make_lbl(text, size_hint_y=None, height=32, color=COLOR_TEXT, font_size="13sp"):
    return Label(
        text=text,
        size_hint_y=size_hint_y, height=height,
        color=color, font_size=font_size,
        halign="left", valign="middle",
        text_size=(None, None),
    )


# ═════════════════════════════════════════════════════════
# 底部导航栏
# ═════════════════════════════════════════════════════════

class BottomBar(BoxLayout):
    def __init__(self, sm, **kw):
        super().__init__(**kw)
        self.sm = sm
        self.size_hint_y = None
        self.height = 52
        self.spacing = 1
        self._btns = []
        items = [("📶 扫描", "scan"), ("📋 历史", "history"), ("⚙ 管理", "admin")]
        for label, name in items:
            b = Button(
                text=label,
                size_hint_y=1, size_hint_x=1,
                background_normal="",
                background_color=COLOR_PRIMARY if sm.current == name else (0.35, 0.35, 0.40, 1),
                color=COLOR_WHITE, font_size="13sp",
            )
            b._screen_name = name
            b.bind(on_press=self._on_press)
            self._btns.append(b)
            self.add_widget(b)

    def _on_press(self, btn):
        self.sm.current = btn._screen_name
        for b in self._btns:
            b.background_color = COLOR_PRIMARY if b._screen_name == self.sm.current else (0.35, 0.35, 0.40, 1)

    def refresh(self):
        for b in self._btns:
            b.background_color = COLOR_PRIMARY if b._screen_name == self.sm.current else (0.35, 0.35, 0.40, 1)


# ═════════════════════════════════════════════════════════
# WiFi 绑定弹窗
# ═════════════════════════════════════════════════════════

class WifiBindPopup(Popup):
    def __init__(self, wifi_row, on_saved=None, **kw):
        super().__init__(**kw)
        self.title = "绑定单位"
        self.size_hint = (0.9, 0.55)
        self.wifi_row = wifi_row
        self.on_saved = on_saved
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=12, spacing=8)
        r = self.wifi_row
        info = (
            f"SSID: {r.get('ssid','')}\n"
            f"BSSID: {r.get('bssid','')}\n"
            f"信号: {r.get('signal','')}dBm  "
            f"信道: {r.get('channel','')}  "
            f"频段: {r.get('band','')}\n"
            f"加密: {r.get('encrypt_type','')}  "
            f"厂商: {r.get('vendor','')}"
        )
        root.add_widget(make_lbl(info, size_hint_y=None, height=80, color=COLOR_TEXT, font_size="12sp"))

        # 单位下拉
        root.add_widget(make_lbl("关联单位：", size_hint_y=None, height=24, font_size="12sp"))
        units = database.get_all_units()
        names = ["（未关联）"] + [u["unit_name"] for u in units]
        self.spinner = Spinner(
            text="（未关联）", values=names,
            size_hint_y=None, height=36,
            font_size="13sp",
        )
        # 如果已有关联，选中对应单位
        uid = r.get("unit_id") or 0
        if uid:
            for u in units:
                if u["id"] == uid:
                    self.spinner.text = u["unit_name"]
                    break
        root.add_widget(self.spinner)

        # 按钮
        btn_bar = BoxLayout(size_hint_y=None, height=44, spacing=8)
        btn_ok = make_btn("提交绑定", on_press=self._on_ok, bg=COLOR_SUCCESS)
        btn_cancel = make_btn("取消", on_press=lambda *_: self.dismiss(), bg=COLOR_GRAY)
        btn_bar.add_widget(btn_ok)
        btn_bar.add_widget(btn_cancel)
        root.add_widget(btn_bar)
        self.content = root

    def _on_ok(self, *_):
        uid = None
        if self.spinner.text != "（未关联）":
            units = database.get_all_units()
            for u in units:
                if u["unit_name"] == self.spinner.text:
                    uid = u["id"]
                    break
        database.bind_wifi_unit(self.wifi_row["id"], uid)
        if self.on_saved:
            self.on_saved()
        self.dismiss()


# ═════════════════════════════════════════════════════════
# 单位表单弹窗
# ═════════════════════════════════════════════════════════

class UnitFormPopup(Popup):
    def __init__(self, unit_row=None, on_saved=None, **kw):
        super().__init__(**kw)
        self.title = "编辑单位" if unit_row else "新增单位"
        self.size_hint = (0.9, 0.65)
        self.unit_row = unit_row
        self.on_saved = on_saved
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=12, spacing=8)
        self.inp_name    = TextInput(hint_text="单位名称（必填）", size_hint_y=None, height=36)
        self.inp_credit  = TextInput(hint_text="统一社会信用代码（必填）", size_hint_y=None, height=36)
        self.inp_address = TextInput(hint_text="单位地址（必填）", size_hint_y=None, height=36)
        if self.unit_row:
            self.inp_name.text    = self.unit_row.get("unit_name", "")
            self.inp_credit.text  = self.unit_row.get("credit_code", "")
            self.inp_address.text = self.unit_row.get("address", "")
        for w in [self.inp_name, self.inp_credit, self.inp_address]:
            root.add_widget(w)

        btn_bar = BoxLayout(size_hint_y=None, height=44, spacing=8)
        btn_ok = make_btn("保存", on_press=self._on_ok, bg=COLOR_SUCCESS)
        btn_cancel = make_btn("取消", on_press=lambda *_: self.dismiss(), bg=COLOR_GRAY)
        btn_bar.add_widget(btn_ok)
        btn_bar.add_widget(btn_cancel)
        root.add_widget(btn_bar)
        self.content = root

    def _on_ok(self, *_):
        name, credit, addr = self.inp_name.text.strip(), self.inp_credit.text.strip(), self.inp_address.text.strip()
        if not name or not credit or not addr:
            return
        if self.unit_row:
            database.update_unit(self.unit_row["id"], name, credit, addr)
        else:
            database.add_unit(name, credit, addr)
        if self.on_saved:
            self.on_saved()
        self.dismiss()


# ═════════════════════════════════════════════════════════
# 确认弹窗
# ═════════════════════════════════════════════════════════

class ConfirmPopup(Popup):
    def __init__(self, message, on_confirm=None, **kw):
        super().__init__(**kw)
        self.title = "确认操作"
        self.size_hint = (0.75, 0.35)
        self.on_confirm = on_confirm
        root = BoxLayout(orientation="vertical", padding=16, spacing=12)
        root.add_widget(make_lbl(message, size_hint_y=None, height=40, color=COLOR_TEXT))
        btn_bar = BoxLayout(size_hint_y=None, height=44, spacing=8)
        btn_yes = make_btn("确定", on_press=self._on_yes, bg=COLOR_DANGER)
        btn_no  = make_btn("取消", on_press=lambda *_: self.dismiss(), bg=COLOR_GRAY)
        btn_bar.add_widget(btn_yes)
        btn_bar.add_widget(btn_no)
        root.add_widget(btn_bar)
        self.content = root

    def _on_yes(self, *_):
        if self.on_confirm:
            self.on_confirm()
        self.dismiss()


# ═════════════════════════════════════════════════════════
# 扫描页
# ═════════════════════════════════════════════════════════

class ScanScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = "scan"
        self._scanning = False
        self._auto_save = False
        self._rows = []
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical", spacing=2)

        # 顶部工具栏
        bar = BoxLayout(size_hint_y=None, height=44, spacing=4, padding=[4, 2])
        self.btn_start    = make_btn("开始扫描", on_press=self._on_start)
        self.btn_stop     = make_btn("停止", on_press=self._on_stop, bg=COLOR_DANGER)
        self.btn_clear    = make_btn("清空", on_press=self._on_clear, bg=COLOR_GRAY)
        self.btn_save     = make_btn("手动入库", on_press=self._on_save)
        self.btn_auto     = ToggleButton(text="自动入库", size_hint_y=None, height=40, size_hint_x=1,
                                        background_normal="", background_color=COLOR_GRAY,
                                        color=COLOR_WHITE, font_size="13sp")
        self.btn_auto.bind(on_press=self._on_auto)
        for b in [self.btn_start, self.btn_stop, self.btn_clear, self.btn_save, self.btn_auto]:
            bar.add_widget(b)
        root.add_widget(bar)

        # 列表头
        hdr = BoxLayout(size_hint_y=None, height=28, spacing=2, padding=[4, 0])
        hdr.add_widget(make_lbl("SSID", size_hint_x=2, font_size="11sp", color=COLOR_TEXT_L))
        hdr.add_widget(make_lbl("BSSID", size_hint_x=2, font_size="11sp", color=COLOR_TEXT_L))
        hdr.add_widget(make_lbl("信号", size_hint_x=1, font_size="11sp", color=COLOR_TEXT_L))
        hdr.add_widget(make_lbl("信道", size_hint_x=0.6, font_size="11sp", color=COLOR_TEXT_L))
        hdr.add_widget(make_lbl("频段", size_hint_x=0.8, font_size="11sp", color=COLOR_TEXT_L))
        root.add_widget(hdr)

        # 扫描结果列表
        self.sv = ScrollView()
        self.list_layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=1)
        self.list_layout.bind(minimum_height=self.list_layout.setter("height"))
        self.sv.add_widget(self.list_layout)
        root.add_widget(self.sv)

        # 日志
        self.log_lbl = make_lbl("就绪", size_hint_y=None, height=32, color=COLOR_TEXT_L, font_size="11sp")
        root.add_widget(self.log_lbl)
        self.add_widget(root)

    def _log(self, msg):
        self.log_lbl.text = f"[{ts()}] {msg}"

    def _on_start(self, *_):
        if self._scanning:
            return
        self._scanning = True
        self._log("开始扫描…")
        threading.Thread(target=self._scan_loop, daemon=True).start()

    def _on_stop(self, *_):
        self._scanning = False
        self._log("已停止")

    def _on_clear(self, *_):
        self.list_layout.clear_widgets()
        self._rows = []
        self._log("列表已清空")

    def _on_auto(self, btn):
        self._auto_save = btn.state == "down"
        btn.background_color = COLOR_SUCCESS if self._auto_save else COLOR_GRAY
        self._log(f"自动入库：{'开启' if self._auto_save else '关闭'}")

    def _on_save(self, *_):
        if not self._rows:
            self._log("无数据可保存")
            return
        ok, skip = database.save_wifi_records(self._rows)
        self._log(f"入库：新增 {ok}，跳过 {skip}")
        App.get_running_app().history_screen._load()

    def _scan_loop(self):
        while self._scanning:
            rows = wifi_scanner.scan_wifi()
            self._rows = rows
            def update(dt):
                self.list_layout.clear_widgets()
                for r in rows:
                    item = BoxLayout(size_hint_y=None, height=30, spacing=4)
                    item.add_widget(make_lbl(r['ssid'][:20], size_hint_x=2, font_size="11sp"))
                    item.add_widget(make_lbl(r['bssid'], size_hint_x=2, font_size="10sp", color=COLOR_TEXT_L))
                    item.add_widget(make_lbl(f"{r['signal']}", size_hint_x=1, font_size="11sp"))
                    item.add_widget(make_lbl(str(r['channel']), size_hint_x=0.6, font_size="11sp"))
                    item.add_widget(make_lbl(r['band'], size_hint_x=0.8, font_size="11sp"))
                    item.bind(on_touch_down=lambda inst, touch, rr=r: self._on_item_click(inst, touch, rr))
                    self.list_layout.add_widget(item)
                self._log(f"扫描到 {len(rows)} 个")
            Clock.schedule_once(update)
            if self._auto_save and rows:
                database.save_wifi_records(rows)
            # 等待 5 秒
            for _ in range(50):
                if not self._scanning:
                    break
                import time; time.sleep(0.1)

    def _on_item_click(self, inst, touch, row):
        if not inst.collide_point(*touch.pos):
            return
        popup = WifiBindPopup(row, on_saved=lambda: self._log(f"已绑定：{row['ssid']}"))
        popup.open()


# ═════════════════════════════════════════════════════════
# 历史数据页
# ═════════════════════════════════════════════════════════

class HistoryScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = "history"
        self._page = 1
        self._page_size = 50
        self._total = 0
        self._selected_id = None
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical", spacing=2)

        # 搜索栏
        bar = BoxLayout(size_hint_y=None, height=44, spacing=4, padding=[4, 2])
        self.inp_ssid   = TextInput(hint_text="SSID", size_hint_x=1, font_size="12sp")
        self.inp_bssid  = TextInput(hint_text="BSSID", size_hint_x=1, font_size="12sp")
        self.spn_band    = Spinner(text="全部频段", values=["全部频段", "2.4G", "5G"],
                                   size_hint_x=0.8, font_size="12sp")
        btn_query = make_btn("查询", on_press=self._on_query, size_hint_x=0.6)
        btn_reset = make_btn("重置", on_press=self._on_reset, size_hint_x=0.6, bg=COLOR_GRAY)
        for w in [self.inp_ssid, self.inp_bssid, self.spn_band, btn_query, btn_reset]:
            bar.add_widget(w)
        root.add_widget(bar)

        # 列表头
        hdr = BoxLayout(size_hint_y=None, height=28, spacing=2, padding=[4, 0])
        for t in ["ID", "SSID", "BSSID", "信号", "信道", "频段", "单位"]:
            hdr.add_widget(make_lbl(t, size_hint_x=1, font_size="11sp", color=COLOR_TEXT_L))
        root.add_widget(hdr)

        # 列表
        self.sv = ScrollView()
        self.list_layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=1)
        self.list_layout.bind(minimum_height=self.list_layout.setter("height"))
        self.sv.add_widget(self.list_layout)
        root.add_widget(self.sv)

        # 底部分页 + 操作
        bot = BoxLayout(size_hint_y=None, height=44, spacing=4, padding=[4, 2])
        self.btn_prev  = make_btn("上一页", on_press=self._on_prev, size_hint_x=0.8)
        self.page_lbl = make_lbl("第1页", size_hint_x=1, font_size="12sp")
        self.btn_next  = make_btn("下一页", on_press=self._on_next, size_hint_x=0.8)
        btn_del    = make_btn("删除选中", on_press=self._on_delete, bg=COLOR_DANGER, size_hint_x=1)
        btn_exp    = make_btn("导出Excel", on_press=self._on_export, size_hint_x=1)
        for w in [self.btn_prev, self.page_lbl, self.btn_next, btn_del, btn_exp]:
            bot.add_widget(w)
        root.add_widget(bot)
        self.add_widget(root)

    def on_enter(self):
        self._load()

    def _load(self):
        band = self.spn_band.text if self.spn_band.text != "全部频段" else ""
        rows, total = database.query_wifi(
            ssid=self.inp_ssid.text.strip(),
            bssid=self.inp_bssid.text.strip(),
            band=band,
            page=self._page,
            page_size=self._page_size,
        )
        self._total = total
        self.list_layout.clear_widgets()
        for r in rows:
            item = BoxLayout(size_hint_y=None, height=30, spacing=2)
            item.add_widget(make_lbl(str(r['id']), size_hint_x=0.5, font_size="10sp", color=COLOR_TEXT_L))
            item.add_widget(make_lbl(r['ssid'][:18], size_hint_x=1.5, font_size="11sp"))
            item.add_widget(make_lbl(r['bssid'], size_hint_x=1.5, font_size="10sp", color=COLOR_TEXT_L))
            item.add_widget(make_lbl(str(r['signal']), size_hint_x=0.6, font_size="11sp"))
            item.add_widget(make_lbl(str(r['channel']), size_hint_x=0.5, font_size="11sp"))
            item.add_widget(make_lbl(r['band'], size_hint_x=0.6, font_size="11sp"))
            item.add_widget(make_lbl(r.get('unit_name', ''), size_hint_x=1, font_size="11sp"))
            item.bind(on_touch_down=lambda inst, touch, rr=r: self._on_item_click(inst, touch, rr))
            self.list_layout.add_widget(item)
        tp = max(1, (total + self._page_size - 1) // self._page_size)
        self.page_lbl.text = f"第{self._page}/{tp}页  共{total}条"

    def _on_query(self, *_):
        self._page = 1
        self._load()

    def _on_reset(self, *_):
        self.inp_ssid.text = ""
        self.inp_bssid.text = ""
        self.spn_band.text = "全部频段"
        self._page = 1
        self._load()

    def _on_prev(self, *_):
        if self._page > 1:
            self._page -= 1
            self._load()

    def _on_next(self, *_):
        tp = max(1, (self._total + self._page_size - 1) // self._page_size)
        if self._page < tp:
            self._page += 1
            self._load()

    def _on_item_click(self, inst, touch, row):
        if not inst.collide_point(*touch.pos):
            return
        self._selected_id = row['id']
        popup = WifiBindPopup(row, on_saved=self._load)
        popup.open()

    def _on_delete(self, *_):
        if not hasattr(self, '_selected_id') or not self._selected_id:
            return
        def do_del():
            database.delete_wifi(self._selected_id)
            self._selected_id = None
            self._load()
        popup = ConfirmPopup(f"确定删除 ID={self._selected_id} 的记录？", on_confirm=do_del)
        popup.open()

    def _on_export(self, *_):
        rows, _ = database.query_wifi(page=1, page_size=999999)
        ok, msg = export_utils.do_export(rows, "xlsx")
        App.get_running_app().root_window.children[0].children[0].log_lbl.text = f"[{ts()}] {'导出成功：' + msg if ok else '导出失败：' + msg}"


# ═════════════════════════════════════════════════════════
# 管理后台页
# ═════════════════════════════════════════════════════════

class AdminScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = "admin"
        self._page = 1
        self._page_size = 30
        self._total = 0
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical", spacing=2)

        # 顶部操作栏
        bar = BoxLayout(size_hint_y=None, height=44, spacing=4, padding=[4, 2])
        btn_add   = make_btn("新增单位", on_press=self._on_add, size_hint_x=1)
        btn_import = make_btn("批量导入", on_press=self._on_import, size_hint_x=1, bg=COLOR_PRIMARY_L)
        btn_del   = make_btn("批量删除", on_press=self._on_batch_del, size_hint_x=1, bg=COLOR_DANGER)
        btn_back  = make_btn("返回主界面", on_press=self._on_back, size_hint_x=1, bg=COLOR_GRAY)
        for w in [btn_add, btn_import, btn_del, btn_back]:
            bar.add_widget(w)
        root.add_widget(bar)

        # 搜索栏
        search_bar = BoxLayout(size_hint_y=None, height=40, spacing=4, padding=[4, 0])
        self.inp_search = TextInput(hint_text="搜索单位名称…", size_hint_x=1, font_size="12sp")
        btn_search  = make_btn("搜索", on_press=self._on_search, size_hint_x=0.6)
        search_bar.add_widget(self.inp_search)
        search_bar.add_widget(btn_search)
        root.add_widget(search_bar)

        # 列表头
        hdr = BoxLayout(size_hint_y=None, height=28, spacing=2, padding=[4, 0])
        for t in ["ID", "单位名称", "信用代码", "地址", "操作"]:
            hdr.add_widget(make_lbl(t, size_hint_x=1, font_size="11sp", color=COLOR_TEXT_L))
        root.add_widget(hdr)

        # 列表
        self.sv = ScrollView()
        self.list_layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=1)
        self.list_layout.bind(minimum_height=self.list_layout.setter("height"))
        self.sv.add_widget(self.list_layout)
        root.add_widget(self.sv)

        # 底部分页
        bot = BoxLayout(size_hint_y=None, height=44, spacing=4, padding=[4, 2])
        self.btn_prev = make_btn("上一页", on_press=self._on_prev, size_hint_x=0.8)
        self.page_lbl = make_lbl("第1页", size_hint_x=1, font_size="12sp")
        self.btn_next = make_btn("下一页", on_press=self._on_next, size_hint_x=0.8)
        bot.add_widget(self.btn_prev)
        bot.add_widget(self.page_lbl)
        bot.add_widget(self.btn_next)
        root.add_widget(bot)
        self.add_widget(root)

    def on_enter(self):
        self._load()

    def _load(self):
        keyword = self.inp_search.text.strip()
        rows, total = database.query_units(keyword=keyword, page=self._page, page_size=self._page_size)
        self._total = total
        self.list_layout.clear_widgets()
        for r in rows:
            item = BoxLayout(size_hint_y=None, height=32, spacing=2)
            item.add_widget(make_lbl(str(r['id']), size_hint_x=0.4, font_size="10sp", color=COLOR_TEXT_L))
            item.add_widget(make_lbl(r['unit_name'][:14], size_hint_x=1.5, font_size="11sp"))
            item.add_widget(make_lbl(r['credit_code'][:16], size_hint_x=1.5, font_size="10sp", color=COLOR_TEXT_L))
            item.add_widget(make_lbl(r['address'][:16], size_hint_x=1.5, font_size="10sp", color=COLOR_TEXT_L))
            btn_edit = make_btn("编辑", on_press=lambda inst, rr=r: self._on_edit(inst, rr), size_hint_x=0.6, bg=COLOR_PRIMARY_L)
            btn_del  = make_btn("删除", on_press=lambda inst, rr=r: self._on_del(inst, rr), size_hint_x=0.6, bg=COLOR_DANGER)
            item.add_widget(btn_edit)
            item.add_widget(btn_del)
            self.list_layout.add_widget(item)
        tp = max(1, (total + self._page_size - 1) // self._page_size)
        self.page_lbl.text = f"第{self._page}/{tp}页  共{total}条"

    def _on_add(self, *_):
        popup = UnitFormPopup(on_saved=self._load)
        popup.open()

    def _on_edit(self, _, row):
        popup = UnitFormPopup(unit_row=row, on_saved=self._load)
        popup.open()

    def _on_del(self, _, row):
        def do_del():
            database.delete_unit(row['id'])
            self._load()
        popup = ConfirmPopup(f"确定删除单位【{row['unit_name']}】？", on_confirm=do_del)
        popup.open()

    def _on_batch_del(self, *_):
        def do_del():
            database.delete_all_units()
            self._page = 1
            self._load()
        popup = ConfirmPopup("确定删除所有单位？此操作不可恢复！", on_confirm=do_del)
        popup.open()

    def _on_import(self, *_):
        content = BoxLayout(orientation="vertical", padding=12, spacing=8)
        fc = FileChooserListView(filters=["*.xlsx", "*.xls", "*.csv"])
        content.add_widget(fc)
        btn_bar = BoxLayout(size_hint_y=None, height=44, spacing=8)
        btn_ok = make_btn("导入", on_press=lambda *_: self._do_import(fc.path, fc.selection), bg=COLOR_SUCCESS)
        btn_cancel = make_btn("取消", on_press=lambda *_: popup.dismiss(), bg=COLOR_GRAY)
        btn_bar.add_widget(btn_ok)
        btn_bar.add_widget(btn_cancel)
        content.add_widget(btn_bar)
        popup = Popup(title="选择导入文件", content=content, size_hint=(0.9, 0.8))
        popup.open()

    def _do_import(self, path, selection):
        fp = selection[0] if selection else path
        if not fp or not os.path.isfile(fp):
            return
        ok, skip, msg = database.import_units_from_file(fp)
        popup = ConfirmPopup(f"导入完成！\n成功：{ok} 条\n跳过：{skip} 条\n{msg}", on_confirm=lambda: self._load())
        popup.open()

    def _on_search(self, *_):
        self._page = 1
        self._load()

    def _on_prev(self, *_):
        if self._page > 1:
            self._page -= 1
            self._load()

    def _on_next(self, *_):
        tp = max(1, (self._total + self._page_size - 1) // self._page_size)
        if self._page < tp:
            self._page += 1
            self._load()

    def _on_back(self, *_):
        App.get_running_app().sm.current = "scan"


# ═════════════════════════════════════════════════════════
# 主应用
# ═════════════════════════════════════════════════════════

class WifiToolApp(App):
    def build(self):
        database.init_db()
        root = BoxLayout(orientation="vertical")
        self.sm = ScreenManager()
        self.scan_screen   = ScanScreen()
        self.history_screen = HistoryScreen()
        self.admin_screen  = AdminScreen()
        for s in [self.scan_screen, self.history_screen, self.admin_screen]:
            self.sm.add_widget(s)
        root.add_widget(self.sm)
        self.bar = BottomBar(self.sm)
        root.add_widget(self.bar)
        return root

    def on_stop(self):
        database.close_db()


# ═════════════════════════════════════════════════════════

def main():
    WifiToolApp().run()

if __name__ == "__main__":
    main()

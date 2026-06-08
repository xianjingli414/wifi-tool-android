# -*- coding: utf-8 -*-
"""
database.py - SQLite 数据库操作，Windows + Android 通用
"""

import os
import sys
import sqlite3
import datetime


def get_db_path() -> str:
    """返回数据库文件的绝对路径"""
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "wifi_data.db")


def get_conn():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
CREATE TABLE IF NOT EXISTS unit_info (
    id          INTEGER  PRIMARY KEY AUTOINCREMENT,
    unit_name   TEXT     NOT NULL UNIQUE,
    credit_code TEXT     NOT NULL,
    address     TEXT     NOT NULL,
    create_time DATETIME DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS wifi_info (
    id           INTEGER  PRIMARY KEY AUTOINCREMENT,
    ssid         TEXT     NOT NULL,
    bssid        TEXT     NOT NULL UNIQUE,
    signal       INTEGER,
    channel      INTEGER,
    encrypt_type TEXT,
    band         TEXT,
    vendor       TEXT,
    collect_time DATETIME DEFAULT (datetime('now','localtime')),
    unit_id      INTEGER,
    FOREIGN KEY (unit_id) REFERENCES unit_info(id) ON DELETE SET NULL
);
""")


# ── WiFi 入库 ─────────────────────────────────────────────

def save_wifi_records(records: list) -> tuple:
    ok = skip = 0
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        for r in records:
            try:
                conn.execute(
                    "INSERT INTO wifi_info (ssid,bssid,signal,channel,encrypt_type,band,vendor,collect_time) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (r["ssid"], r["bssid"], r["signal"], r["channel"],
                     r["encrypt_type"], r["band"], r["vendor"], now))
                ok += 1
            except sqlite3.IntegrityError:
                skip += 1
    return ok, skip


# ── WiFi 查询 / 删除 / 绑定 ──────────────────────────────

def query_wifi(ssid="", bssid="", band="", unit_id=None,
               page=1, page_size=50) -> tuple:
    conds = []
    params = []
    if ssid:
        conds.append("w.ssid LIKE ?")
        params.append(f"%{ssid}%")
    if bssid:
        conds.append("w.bssid LIKE ?")
        params.append(f"%{bssid}%")
    if band:
        conds.append("w.band = ?")
        params.append(band)
    if unit_id is not None:
        conds.append("w.unit_id = ?")
        params.append(unit_id)
    where = ("WHERE " + " AND ".join(conds)) if conds else ""
    sql_count = (f"SELECT COUNT(*) FROM wifi_info w "
                 f"LEFT JOIN unit_info u ON w.unit_id=u.id {where}")
    sql_data = (f"SELECT w.id,w.ssid,w.bssid,w.signal,w.channel,"
                 f"w.encrypt_type,w.band,w.vendor,w.collect_time,"
                 f"COALESCE(u.unit_name,'') AS unit_name "
                 f"FROM wifi_info w LEFT JOIN unit_info u ON w.unit_id=u.id "
                 f"{where} ORDER BY w.collect_time DESC LIMIT ? OFFSET ?")
    offset = (page - 1) * page_size
    with get_conn() as conn:
        total = conn.execute(sql_count, params).fetchone()[0]
        rows  = conn.execute(sql_data, params + [page_size, offset]).fetchall()
        rows = [dict(r) for r in rows]
    return rows, total


def delete_wifi_by_ids(ids: list):
    ph = ",".join("?" * len(ids))
    with get_conn() as conn:
        conn.execute(f"DELETE FROM wifi_info WHERE id IN ({ph})", ids)


def bind_wifi_unit(wifi_id: int, unit_id):
    with get_conn() as conn:
        conn.execute("UPDATE wifi_info SET unit_id=? WHERE id=?",
                     (unit_id, wifi_id))


def get_wifi_by_id(wifi_id: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT w.*,COALESCE(u.unit_name,'') AS unit_name "
            "FROM wifi_info w LEFT JOIN unit_info u ON w.unit_id=u.id "
            "WHERE w.id=?", (wifi_id,)
        ).fetchone()
        return dict(row) if row else None


# ── 单位操作 ────────────────────────────────────────────────

def query_units(keyword="", page=1, page_size=50) -> tuple:
    conds = []
    params = []
    if keyword:
        conds.append("unit_name LIKE ?")
        params.append(f"%{keyword}%")
    where = ("WHERE " + " AND ".join(conds)) if conds else ""
    with get_conn() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) FROM unit_info {where}", params
        ).fetchone()[0]
        rows = conn.execute(
            f"SELECT id,unit_name,credit_code,address,create_time "
            f"FROM unit_info {where} ORDER BY id DESC LIMIT ? OFFSET ?",
            params + [page_size, (page - 1) * page_size]
        ).fetchall()
        rows = [dict(r) for r in rows]
    return rows, total


def get_all_units() -> list:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id,unit_name FROM unit_info ORDER BY unit_name"
        ).fetchall()
        return [dict(r) for r in rows]


def add_unit(name, code, addr) -> bool:
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO unit_info (unit_name,credit_code,address) VALUES (?,?,?)",
                (name, code, addr))
        return True
    except sqlite3.IntegrityError:
        return False


def update_unit(uid, name, code, addr) -> bool:
    try:
        with get_conn() as conn:
            conn.execute(
                "UPDATE unit_info SET unit_name=?,credit_code=?,address=? WHERE id=?",
                (name, code, addr, uid))
        return True
    except sqlite3.IntegrityError:
        return False


def delete_units_by_ids(ids: list):
    ph = ",".join("?" * len(ids))
    with get_conn() as conn:
        conn.execute(f"DELETE FROM unit_info WHERE id IN ({ph})", ids)


def delete_wifi(wifi_id: int):
    delete_wifi_by_ids([wifi_id])

def delete_unit(unit_id: int):
    delete_units_by_ids([unit_id])

def delete_all_units():
    with get_conn() as conn:
        conn.execute("DELETE FROM unit_info")

def close_db():
    pass  # SQLite 连接由上下文管理器自动关闭

# ── 导入导出 ────────────────────────────────────────────────

def import_units_from_data(rows: list) -> tuple:
    ok = fail = 0
    reasons = []
    with get_conn() as conn:
        for i, r in enumerate(rows, start=1):
            name = str(r.get("unit_name", r.get("单位名称", ""))).strip()
            code = str(r.get("credit_code", r.get("统一社会信用代码", ""))).strip()
            addr = str(r.get("address", r.get("地址", ""))).strip()
            if not name:
                fail += 1
                reasons.append(f"第{i}行：单位名称为空")
                continue
            if not code:
                fail += 1
                reasons.append(f"第{i}行：信用代码为空")
                continue
            if not addr:
                fail += 1
                reasons.append(f"第{i}行：地址为空")
                continue
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO unit_info (unit_name,credit_code,address) VALUES (?,?,?)",
                    (name, code, addr))
                if conn.execute("SELECT changes()").fetchone()[0] == 0:
                    fail += 1
                    reasons.append(f"第{i}行：单位「{name}」重复")
                    continue
                ok += 1
            except Exception as e:
                fail += 1
                reasons.append(f"第{i}行：{e}")
    return ok, fail, reasons


def import_units_from_file(filepath: str) -> tuple:
    """从 Excel/CSV 文件导入单位数据"""
    try:
        import openpyxl
        wb = openpyxl.load_workbook(filepath, read_only=True)
        ws = wb.active
        headers = [cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1))]
        rows_data = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            rows_data.append(dict(zip(headers, row)))
        wb.close()
    except Exception:
        import csv
        with open(filepath, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows_data = list(reader)
    ok, fail, reasons = import_units_from_data(rows_data)
    msg = "; ".join(reasons[:10]) if reasons else ""
    return ok, fail, msg

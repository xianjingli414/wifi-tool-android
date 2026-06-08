# WiFi 采集管理工具 - Android 版

基于 Python + KivyMD + Briefcase 开发的 Android WiFi 采集管理工具。

## 目录结构

```
wifi_tool_android/
├── pyproject.toml                  # Briefcase 配置
├── resources/                       # 图标等资源
├── src/wifi_tool_android/
│   ├── __init__.py
│   ├── __main__.py                 # 程序入口
│   ├── app.py                      # KivyMD App 主类
│   ├── database.py                 # SQLite 数据库操作
│   ├── wifi_scanner.py             # WiFi 扫描（Windows + Android）
│   ├── unit_manager.py             # 单位管理业务逻辑
│   ├── export_utils.py             # Excel/CSV 导出
│   └── screens/
│       ├── __init__.py
│       ├── scan_screen.kv          # 扫描页布局
│       ├── scan_screen.py          # 扫描页逻辑
│       ├── history_screen.kv       # 历史数据页布局
│       ├── history_screen.py       # 历史数据页逻辑
│       ├── admin_screen.kv         # 后台管理页布局
│       ├── admin_screen.py         # 后台管理页逻辑
│       └── dialogs.py             # 弹窗组件
└── build/                          # Briefcase 构建输出
```

## 构建步骤

### 环境要求
- Python 3.9+
- JDK 17
- Android SDK + Build Tools 34.0.0
- Android NDK r25c

### 本地构建 APK

```bash
# 1. 安装依赖
pip install kivy kivymd openpyxl briefcase

# 2. 创建 Android 项目
briefcase create android

# 3. 构建 APK（调试版）
briefcase build android

# 4. 打包签名 APK（发布版）
briefcase package android

# 生成的 APK 位于：
# build/wifi_tool_android/android/gradle/APP/release/app-release-unsigned.apk
```

### 用 Briefcase 直接运行到手机

```bash
# 手机开启 USB 调试，连接电脑
briefcase run android -d
```

## 权限说明（Android）

| 权限 | 用途 |
|------|------|
| ACCESS_FINE_LOCATION | WiFi 扫描需要位置权限（Android 6+） |
| ACCESS_COARSE_LOCATION | 同上，粗略位置 |
| ACCESS_WIFI_STATE | 读取 WiFi 状态 |
| CHANGE_WIFI_STATE | 触发 WiFi 扫描 |
| READ_PHONE_STATE | 设备标识（可选） |

## 使用说明

1. 安装 APK 后，首次启动授予位置权限
2. 底部导航栏切换：📶 扫描 / 📋 历史 / ⚙️ 管理
3. 扫描页点击「开始扫描」采集周边 WiFi
4. 长按列表项可绑定单位
5. 历史页支持搜索、导出、删除
6. 管理页维护单位信息，支持批量导入

---

*兼容华为、小米、OPPO、vivo 等 Android 8.0+ 设备*

*Last build trigger: 2026-06-09 04:05:22.181229*

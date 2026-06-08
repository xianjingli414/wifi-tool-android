[app]
# 应用名称
title = WiFi采集管理工具
# 包名
package.name = wifi_tool
package.domain = com.example.wifitool

# 源代码
source.dir = .
source.include_exts = py,png,jpg,kv,db
source.exclude_exts = spec

# 应用版本
version = 1.0.0
version.code = 1

# 要求
requirements = python3,kivy>=2.3.0,openpyxl,pyjnius,plyer

# 权限
android.permissions = ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,ACCESS_WIFI_STATE,CHANGE_WIFI_STATE,READ_PHONE_STATE,INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.features = 

# Android API
android.api = 34
android.minapi = 24
android.targetapi = 34
android.ndk = 25b
android.sdk_tools = 34.0.0

# 图标
icon.filename = %(source.dir)s/icon.png
# 预设图标（如果没有）
icon.filename = 

# 屏幕方向
orientation = portrait

# 全屏
fullscreen = 0

# 启动器
presplash.filename = %(source.dir)s/presplash.png
presplash.filename = 

# 白色背景
presplash.color = #FFFFFF

# 主程序
app.main = app

[buildozer]
# 构建版本
buildozer.version = 2.0

# 不清理
buildozer.bin = .buildozer

# 日志级别
log_level = 2

# 警告抑制
warn_on_root = 1

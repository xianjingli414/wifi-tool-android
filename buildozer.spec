[app]
# 应用名称
title = WiFi采集管理工具
package.name = wifi_tool
package.domain = org.example

# 源代码目录
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,db,txt,md

# 版本
version = 1.0.0

# 依赖
requirements = python3,kivy,openpyxl,sqlite3,random

# 应用图标（如果有）
#icon = %(source.dir)s/icon.png

# 启动图片（如果有）
#presplash.filename = %(source.dir)s/presplash.png

# 屏幕方向
orientation = portrait
osx.python_version = 3
osx.kivy_version = 2.3.0
fullscreen = 0

[android]
# Android 权限
android.permissions = ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,ACCESS_WIFI_STATE,CHANGE_WIFI_STATE,READ_PHONE_STATE

# Android API 版本
android.api = 34
android.minapi = 24
android.ndk = 25b
android.sdk = 34
android.gradle_dependencies = 'com.android.support:support-v4:28.0.0'
android.allow_backup = True
android.arch = arm64-v8a

# 应用名称和版本
android.stringversion = 1.0.0
android.version_code = 1

[ios]
# iOS 配置（暂时不需要）

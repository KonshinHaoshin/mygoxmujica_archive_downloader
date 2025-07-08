# 🎀 mygoxmujica_archive_downloader

一个为 WebGAL 项目的 mygoxmujica 系列资源设计的图形化 GitHub 下载器。支持从指定仓库快速下载角色改模、动作模组、工具等分类资源，支持多镜像加速、二次元 UI 风格美化、断点中断、子路径保存等实用功能。

---

## ✨ 功能亮点

- ✅ 自动加载 GitHub 仓库下的资源目录（支持子目录递归）
- ✅ 支持文件筛选搜索与分类浏览
- ✅ 支持 jsDelivr、raw.githubusercontent、ghproxy 镜像加速
- ✅ 支持文件大小显示与下载进度条展示
- ✅ 可中断下载
- ✅ 支持粉色樱花系 UI 样式美化
- ✅ 一键打包为独立 `.exe` 文件（免 Python 运行）

---

## 🧩 项目结构说明

```text
mygoxmujica_archive_downloader/
├── main.py                   # 程序入口
├── ui_main.py                # 主界面逻辑
├── github_api.py             # GitHub 文件加载逻辑
├── downloader.py             # 下载工具函数
├── download_thread.py        # 下载线程支持
├── style.qss                 # 粉色樱花 UI 样式表
├── icon.png / icon.ico       # 图标资源
├── down_arrow_cute.png       # 下拉框箭头图标
└── README.md                 # 使用说明
```

------

## 🚀 使用方法

### 方式一：源码运行

确保你已安装 Python 3.8+ 和 PyQt5：

```bash
python main.py
```

### 方式二：使用release的打包exe





## 🌐 镜像源说明

| 镜像源       | 特性说明                                               |
| ------------ | ------------------------------------------------------ |
| `jsdelivr` ✅ | 推荐：国内稳定，适合小中型文件，自动缓存，更新稍有延迟 |
| `raw`        | 实时直连 GitHub，适合调试，但国内经常失败              |
| `ghproxy`    | 备用方案，目前不稳定，频繁超时                         |

## 📂 当前仓库资源说明（[mygoxmujica_archive](https://github.com/KonshinHaoshin/mygoxmujica_archive)）

| 分类     | 内容                                        |
| -------- | ------------------------------------------- |
| 改模     | 通用 PSD、服装替换、角色立绘合成资源        |
| 动作模组 | `.mtn` 动作、`.exp.json` 表情切换、动画组合 |
| 工具     | Live2D 转换、导出辅助脚本与运行工具         |

## 📮 联系作者

- B站：[东山燃灯寺的个人空间-东山燃灯寺个人主页-哔哩哔哩视频](https://space.bilibili.com/296330875?spm_id_from=333.1007.0.0)

- GitHub：[KonshinHaoshin](https://github.com/KonshinHaoshin)

  

## 📜 License

MIT License - 欢迎自由使用和改进！


## 打包方式
```bash
pyinstaller -w -F main.py --icon=icon.ico --add-data "style.qss;." --add-data "down_arrow_cute.png;." --add-data "icon.png;."
```
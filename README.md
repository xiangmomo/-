# 自动监控文件夹进行视频压缩，提取字幕后覆盖原文件功能






# 监控目录，注意 Windows 路径的转义问题，建议使用原始字符串
MONITOR_DIR = r'D:\下载文件夹\动漫\RSS'
# 轮询间隔时间（秒）
POLL_INTERVAL = 1000
# 记录已处理文件的文本文件
PROCESSED_FILES_LOG = 'processed_files.txt'
# 记录失败文件的文本文件
FAILED_FILES_LOG = 'failed_files.txt'
# 指定 outmp4 文件夹的统一输出路径
OUTMP4_BASE_DIR = r'D:\下载文件夹\临时\output_videos'
# 临时字幕文件夹
TEMP_SUBTITLE_DIR = r'D:\下载文件夹\临时\temp_subtitles'


配置main.py 里面的配置
1.定时监控某个文件夹，包含子文件夹 有新文件就自动进行检测是否有字幕 有就提取然后写到源文件夹
2.定时监控某个文件夹，有新视频就进行压缩，压缩完成后自动自动覆盖源文件，大概可以压40% 具体看视频质量
以及处理的会自动记录到txt 监控时会跳过里面的文件



### FFmpeg 安装方法 Windows 系统
1. 访问 FFmpeg 官方下载页面 下载 Windows 版本的 FFmpeg。
2. 解压下载的压缩包。
3. 将解压后的 bin 目录路径添加到系统环境变量 PATH 中。 命令行安装（使用 Chocolatey）
如果你已经安装了 Chocolatey 包管理器，可以使用以下命令安装 FFmpeg：

```
choco install ffmpeg
```
安装完成后，你就可以正常运行 `main.py` 脚本了。

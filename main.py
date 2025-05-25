import os
import time
import subprocess
import shutil
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='log.txt')

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

# 加载文件列表
def load_file_list(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return set(os.path.normcase(os.path.normpath(line.strip())) for line in f.readlines())
    else:
        return set()

# 保存文件列表
def save_file_list(file_path, file_set):
    with open(file_path, 'w', encoding='utf-8') as f:
        for path in file_set:
            f.write(path + '\n')

# 加载已处理的文件列表 
def load_processed_files():
    return load_file_list(PROCESSED_FILES_LOG)

# 保存已处理的文件列表 
def save_processed_files(processed_files):
    save_file_list(PROCESSED_FILES_LOG, processed_files)

# 加载失败的文件列表 
def load_failed_files():
    return load_file_list(FAILED_FILES_LOG)

# 保存失败的文件列表 
def save_failed_files(failed_files):
    save_file_list(FAILED_FILES_LOG, failed_files)

# 解码输出
def decode_output(output):
    encodings = ['utf-8', 'gbk', 'gb2312', 'big5']
    for encoding in encodings:
        try:
            return output.decode(encoding)
        except UnicodeDecodeError:
            continue
    return None

# 检查视频是否有字幕流 
def has_subtitles(input_video_path):
    try:
        command = [ 
            'ffprobe', 
            '-v', 'quiet', 
            '-print_format', 'json', 
            '-show_streams', 
            input_video_path 
        ] 
        result = subprocess.run(command, capture_output=True, check=True)
        stdout = decode_output(result.stdout)
        if stdout is None:
            logging.error('无法使用任何编码解码 ffprobe 输出。')
            failed_files = load_failed_files()
            failed_files.add(os.path.normcase(os.path.normpath(input_video_path)))
            save_failed_files(failed_files)
            return False
        streams = json.loads(stdout)['streams']
        for stream in streams:
            if stream.get('codec_type') == 'subtitle':
                return True
        logging.info(f'视频 {input_video_path} 中未检测到字幕流。')
        return False
    except subprocess.CalledProcessError as e:
        logging.error(f'检查视频 {input_video_path} 是否有字幕时出错: {e}')
        failed_files = load_failed_files()
        failed_files.add(os.path.normcase(os.path.normpath(input_video_path)))
        save_failed_files(failed_files)
        return False
    except Exception as e:
        logging.error(f'发生未知错误: {e}')
        failed_files = load_failed_files()
        failed_files.add(os.path.normcase(os.path.normpath(input_video_path)))
        save_failed_files(failed_files)
        return False

# 提取字幕 
def extract_subtitles(input_video_path, output_subtitle_path):
    try:
        # 构建 FFmpeg 命令 
        command = [ 
            'ffmpeg', 
            '-y',  # 覆盖已存在的文件 
            '-i', input_video_path, 
            '-map', '0:s:0',  # 选择第一个字幕流 
            output_subtitle_path 
        ] 

        # 执行 FFmpeg 命令 
        subprocess.run(command, check=True)
        logging.info(f'字幕已成功提取到 {output_subtitle_path}')
        # 生成源文件夹的字幕路径
        source_subtitle_path = os.path.join(os.path.dirname(input_video_path), os.path.basename(output_subtitle_path))
        try:
            shutil.move(output_subtitle_path, source_subtitle_path)
            logging.info(f'已将字幕文件移动到源文件夹: {source_subtitle_path}')
        except Exception as e:
            logging.error(f'移动字幕文件到源文件夹时出错: {e}')
            failed_files = load_failed_files()
            failed_files.add(os.path.normcase(os.path.normpath(input_video_path)))
            save_failed_files(failed_files)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f'提取字幕时出错: {e}')
        failed_files = load_failed_files()
        failed_files.add(os.path.normcase(os.path.normpath(input_video_path)))
        save_failed_files(failed_files)
        return False
    except Exception as e:
        logging.error(f'发生未知错误: {e}')
        failed_files = load_failed_files()
        failed_files.add(os.path.normcase(os.path.normpath(input_video_path)))
        save_failed_files(failed_files)
        return False

# 在监控文件夹的函数中添加跳过逻辑（假设存在该函数）
def monitor_folder():
    processed_files = load_processed_files()
    failed_files = load_failed_files()
    while True:
        try:
            has_new_files = False
            logging.info(f'开始检查 {MONITOR_DIR} 目录下的新文件...')
            for root, dirs, files in os.walk(MONITOR_DIR):
                # 跳过 outMP4 文件夹，不区分大小写 
                dirs[:] = [d for d in dirs if d.lower() != 'outmp4']
                for file in files:
                    file_path = os.path.join(root, file)
                    # 统一路径格式并转换为小写
                    normalized_file_path = os.path.normcase(os.path.normpath(file_path))
                    if file.lower().endswith(('.mp4', '.mkv')) and normalized_file_path not in processed_files and normalized_file_path not in failed_files:
                        has_new_files = True
                        logging.info(f'发现新文件: {file_path}')
                        # 确保输出目录存在 
                        if not os.path.exists(OUTMP4_BASE_DIR):
                            os.makedirs(OUTMP4_BASE_DIR, exist_ok=True)
                        if not os.path.exists(TEMP_SUBTITLE_DIR):
                            os.makedirs(TEMP_SUBTITLE_DIR, exist_ok=True)
                        # 生成输出路径，不保留原目录结构 
                        output_video_path = os.path.join(OUTMP4_BASE_DIR, os.path.splitext(file)[0] + '.mp4')
                        output_subtitle_path = os.path.join(TEMP_SUBTITLE_DIR, os.path.splitext(file)[0] + '.srt')

                        # 检查是否有字幕 
                        if has_subtitles(file_path):
                            # 提取字幕 
                            extract_subtitles(file_path, output_subtitle_path)

                        # 压缩视频 
                        if 'compress_video' in globals():
                            compress_video(file_path, output_video_path)
                        else:
                            logging.error('compress_video 函数未定义，请检查代码。')

                        # 标记文件为已处理 
                        processed_files.add(normalized_file_path)
                        save_processed_files(processed_files)

            if not has_new_files:
                logging.info('未发现新文件，等待下次检查...')

            # 等待下一次检查 
            time.sleep(POLL_INTERVAL)
        except Exception as e:
            logging.error(f'监控文件夹时发生错误: {e}')
            time.sleep(POLL_INTERVAL)

# 压缩视频的函数
def compress_video(input_video_path, output_video_path):
    try:
        command = [
            'ffmpeg',
            '-y',  # 覆盖已存在的文件
            '-i', input_video_path,
            '-c:v', 'libx264',  # 视频编码器
            '-preset', 'medium',  # 编码速度与压缩率的平衡
            '-crf', '23',  # 视频质量，值越小质量越高
            '-c:a', 'aac',  # 音频编码器
            '-b:a', '128k',  # 音频比特率
            output_video_path
        ]
        subprocess.run(command, check=True)
        logging.info(f'视频已成功压缩到 {output_video_path}')
        # 添加文件覆盖逻辑
        try:
            shutil.move(output_video_path, input_video_path)
            logging.info(f'已用压缩后的文件覆盖原始文件: {input_video_path}')
        except Exception as e:
            logging.error(f'覆盖原始文件时出错: {e}')
            failed_files = load_failed_files()
            failed_files.add(os.path.normcase(os.path.normpath(input_video_path)))
            save_failed_files(failed_files)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f'压缩视频时出错: {e}')
        failed_files = load_failed_files()
        failed_files.add(os.path.normcase(os.path.normpath(input_video_path)))
        save_failed_files(failed_files)
        return False
    except Exception as e:
        logging.error(f'发生未知错误: {e}')
        failed_files = load_failed_files()
        failed_files.add(os.path.normcase(os.path.normpath(input_video_path)))
        save_failed_files(failed_files)
        return False

if __name__ == '__main__':
    try:
        monitor_folder()
    except KeyboardInterrupt:
        print('程序已终止。')
    finally:
        input('按回车键退出...')

       
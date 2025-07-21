import os
import json
import shutil
import argparse
import sys
import signal
from color import text_color_rgb, string_style, RESET, reset_all

# 全局变量，用于跟踪当前处理的索引
current_index_dir = None

def get_indexes(assets_path: str) -> list:
    """
    获取assets/indexes目录下所有索引文件名（不含扩展名）
    
    参数:
        assets_path: assets目录路径
        
    返回:
        索引文件名列表（不含.json扩展名）
    """
    indexes_dir = os.path.join(assets_path, 'indexes')
    if not os.path.exists(indexes_dir):
        return []
    
    return [
        os.path.splitext(f)[0] 
        for f in os.listdir(indexes_dir) 
        if f.endswith('.json')
    ]

def copy_and_mkdir(src: str, dst: str) -> None:
    """复制文件并自动创建目标目录"""
    target_dir = os.path.dirname(dst)
    os.makedirs(target_dir, exist_ok=True)
    shutil.copy2(src, dst)

def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    while size_bytes >= 1024 and unit_index < len(units)-1:
        size_bytes /= 1024
        unit_index += 1
    return f"{size_bytes:.2f}{units[unit_index]}"

# 颜色配置
COLOR_INDEX = text_color_rgb(0, 128, 255)
COLOR_COUNT = text_color_rgb(0, 255, 0)
COLOR_FILE = text_color_rgb(0, 128, 255)
COLOR_PATH = text_color_rgb(128, 128, 0)
COLOR_WARN = text_color_rgb(255, 165, 0)
COLOR_ERROR = text_color_rgb(255, 0, 0)
STYLE_BOLD = string_style('bright')

def cleanup_incomplete_index(index_dir: str) -> None:
    """清理未完成的索引目录"""
    if index_dir and os.path.exists(index_dir):
        print(f"{COLOR_WARN}清理未完成的索引目录: {index_dir}{RESET}")
        try:
            shutil.rmtree(index_dir)
            print(f"{COLOR_WARN}已删除未完成的索引目录{RESET}")
        except Exception as e:
            print(f"{COLOR_ERROR}清理失败: {str(e)}{RESET}")

def signal_handler(sig, frame):
    """处理中断信号 (Ctrl+C)"""
    print(f"\n{COLOR_ERROR}用户中断!{RESET}")
    if current_index_dir:
        cleanup_incomplete_index(current_index_dir)
    reset_all()
    sys.exit(1)

# 注册信号处理器
signal.signal(signal.SIGINT, signal_handler)

def objects_to_resourcespack(assets_dir: str, result_dir: str, indexes: list = None) -> None:
    """
    从assets目录恢复文件到结果目录
    
    参数:
        assets_dir: 包含indexes和objects文件夹的目录
        result_dir: 结果保存目录
        indexes: 要处理的索引名称列表（不含.json扩展名），None表示处理全部索引
    """
    global current_index_dir
    
    # 确保路径标准化
    assets_dir = os.path.normpath(assets_dir)
    result_dir = os.path.normpath(result_dir)
    
    # 验证目录是否存在
    if not os.path.exists(assets_dir):
        raise FileNotFoundError(f"Assets目录不存在: {assets_dir}")
    
    # 创建结果目录
    os.makedirs(result_dir, exist_ok=True)
    
    # 设置索引和对象目录路径
    indexes_path = os.path.join(assets_dir, 'indexes')
    objects_path = os.path.join(assets_dir, 'objects')
    
    # 验证必要的子目录是否存在
    if not os.path.exists(indexes_path):
        raise FileNotFoundError(f"Indexes目录不存在: {indexes_path}")
    if not os.path.exists(objects_path):
        raise FileNotFoundError(f"Objects目录不存在: {objects_path}")
    
    # 获取所有索引文件
    all_indexes_files = [f for f in os.listdir(indexes_path) if f.endswith('.json')]
    
    # 如果没有指定索引，则使用所有索引
    if indexes is None:
        indexes = get_indexes(assets_dir)
    
    # 过滤出需要处理的索引文件
    indexes_files = [
        f"{index}.json" for index in indexes
        if f"{index}.json" in all_indexes_files
    ]
    
    # 检查无效的索引名称
    invalid_indexes = set(indexes) - set(os.path.splitext(f)[0] for f in indexes_files)
    for invalid in invalid_indexes:
        print(f"{COLOR_WARN}警告: 无效的索引名称将被忽略: {invalid}{RESET}")
    
    if not indexes_files:
        print(f"{COLOR_WARN}警告: 没有找到有效的索引文件{RESET}")
        return
    
    total_indexes = len(indexes_files)

    for idx, index_file in enumerate(indexes_files, 1):
        index_name = os.path.splitext(index_file)[0]
        result_index_dir = os.path.join(result_dir, index_name)
        
        # 设置当前处理的索引目录
        current_index_dir = result_index_dir
        
        # 确保索引目录存在
        os.makedirs(result_index_dir, exist_ok=True)
        
        index_file_path = os.path.join(indexes_path, index_file)
        try:
            with open(index_file_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
        except json.JSONDecodeError:
            print(f"{COLOR_ERROR}错误: 无法解析JSON文件: {index_file_path}{RESET}")
            # 删除损坏索引的目录
            cleanup_incomplete_index(result_index_dir)
            continue
        except Exception as e:
            print(f"{COLOR_ERROR}错误: 读取索引文件失败: {index_file_path}{RESET}")
            print(f"{COLOR_ERROR}错误详情: {str(e)}{RESET}")
            cleanup_incomplete_index(result_index_dir)
            continue
        
        objects = index_data.get('objects', {})
        if not objects:
            print(f"{COLOR_WARN}警告: 索引文件中没有对象数据: {index_file}{RESET}")
            # 删除空索引的目录
            cleanup_incomplete_index(result_index_dir)
            continue
            
        total_files = len(objects)
        map_content = []

        for file_idx, (file_path, file_info) in enumerate(objects.items(), 1):
            file_hash = file_info.get('hash')
            if not file_hash:
                print(f"{COLOR_WARN}警告: 文件缺少哈希值: {file_path}{RESET}")
                continue
                
            src_path = os.path.join(objects_path, file_hash[:2], file_hash)
            if not os.path.exists(src_path):
                print(f"{COLOR_WARN}警告: 源文件不存在: {src_path}{RESET}")
                continue
                
            dst_path = os.path.join(result_index_dir, file_path)
            
            # 进度显示
            progress = (
                f"{COLOR_INDEX}{file_idx}{RESET}/"
                f"{COLOR_COUNT}{total_files}{RESET} "
                f"{STYLE_BOLD}{COLOR_COUNT}{index_name}{RESET}("
                f"{COLOR_INDEX}{idx}{RESET}/"
                f"{COLOR_COUNT}{total_indexes}{RESET}):"
                f"{COLOR_FILE}{file_hash}{RESET}->"
                f"{COLOR_PATH}{file_path}{RESET}"
            )
            print(progress)
            
            # 记录映射信息
            file_size = file_info.get('size', 0)
            map_content.append(
                f"{file_path}: {file_hash} "
                f"({format_size(file_size)})"
            )
            
            try:
                copy_and_mkdir(src_path, dst_path)
            except Exception as e:
                print(f"{COLOR_ERROR}错误: 复制文件失败: {src_path} -> {dst_path}{RESET}")
                print(f"{COLOR_ERROR}错误详情: {str(e)}{RESET}")
                # 删除部分复制的索引目录
                cleanup_incomplete_index(result_index_dir)
                # 退出当前索引处理，继续下一个
                break

        # 写入映射文件
        map_file = os.path.join(result_index_dir, '.map.txt')
        try:
            with open(map_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(map_content))
        except Exception as e:
            print(f"{COLOR_ERROR}错误: 写入映射文件失败: {map_file}{RESET}")
            print(f"{COLOR_ERROR}错误详情: {str(e)}{RESET}")
            # 如果写入映射文件失败，但文件已复制，不删除目录
        
        # 完成当前索引处理
        print(f"Process {STYLE_BOLD}{COLOR_INDEX}{index_name}{RESET} done!")
        current_index_dir = None  # 重置当前索引目录

    print(f"All {COLOR_COUNT}{total_indexes}{RESET} processes completed!")

if __name__ == '__main__':
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(
        description='将objects转换为resources pack',
        epilog='示例: python objects_to_resourcespack.py -a c:/assets -r c:/result'
    )
    parser.add_argument('-a', '--assets', 
                        help='包含indexes和objects文件夹的assets目录',
                        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets'))
    parser.add_argument('-r', '--result', 
                        help='结果保存目录',
                        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'result'))
    parser.add_argument('-i', '--indexes', 
                        help='指定要处理的索引名称列表（逗号分隔），默认全部',
                        default=None)
    parser.add_argument('-l', '--list-indexes', 
                        help='列出所有可用的索引名称',
                        action='store_true')
    
    args = parser.parse_args()
    
    # 如果请求列出索引
    if args.list_indexes:
        assets_path = os.path.normpath(args.assets)
        indexes = get_indexes(assets_path)
        
        if not indexes:
            print(f"{COLOR_WARN}未找到任何索引文件{RESET}")
        else:
            print(f"{STYLE_BOLD}可用的索引列表:{RESET}")
            for idx, index_name in enumerate(indexes, 1):
                print(f"  {COLOR_INDEX}{idx}{RESET}. {COLOR_PATH}{index_name}{RESET}")
            print(f"\n共找到 {COLOR_COUNT}{len(indexes)}{RESET} 个索引")
        reset_all()
        exit(0)
    
    # 处理索引参数
    selected_indexes = None
    if args.indexes:
        selected_indexes = [index.strip() for index in args.indexes.split(',')]
    
    # 打印配置信息
    print(f"{STYLE_BOLD}配置:{RESET}")
    print(f"  Assets目录: {COLOR_PATH}{args.assets}{RESET}")
    print(f"  结果目录: {COLOR_PATH}{args.result}{RESET}")
    if selected_indexes:
        print(f"  指定索引: {COLOR_COUNT}{', '.join(selected_indexes)}{RESET}")
    else:
        print(f"  处理索引: {COLOR_COUNT}全部{RESET}")
    print(f"{STYLE_BOLD}开始处理...{RESET}")
    
    try:
        objects_to_resourcespack(args.assets, args.result, selected_indexes)
        reset_all()
    except Exception as e:
        print(f"{COLOR_ERROR}错误: {str(e)}{RESET}")
        reset_all()
        exit(1)
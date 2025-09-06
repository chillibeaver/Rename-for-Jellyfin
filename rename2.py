import os
import re
import sys


def rename_episodes(path='.', prefix='Episode'):
    """识别并重命名剧集文件"""
    # 匹配各种集数格式的正则表达式
    patterns = [
        r'[Ee](?:p|pisode)?[\s._-]?(\d+)',  # E01, EP01, Episode1
        r'第\s*(\d+)\s*[集话]',               # 第1集, 第1话
        r'[\[【]\s*(\d+)\s*[\]】]',          # [01], 【01】
        r'(?:^|\D)(\d{1,3})(?:\D|$)',        # 独立的数字
    ]

    for file in os.listdir(path):
        if not os.path.isfile(os.path.join(path, file)):
            continue

        name, ext = os.path.splitext(file)

        # 尝试所有模式匹配集数
        for pattern in patterns:
            match = re.search(pattern, name)
            if match:
                ep_num = int(match.group(1))
                new_name = f"{prefix} {ep_num:02d}{ext}"

                if file != new_name:
                    old_path = os.path.join(path, file)
                    new_path = os.path.join(path, new_name)

                    try:
                        os.rename(old_path, new_path)
                        print(f"✓ {file} → {new_name}")
                    except Exception as e:
                        print(f"✗ {file}: {e}")
                break


if __name__ == "__main__":
    # 使用方法：python rename.py [目录] [前缀]
    path = ''

    while not os.path.isdir(path):
        path = input("Enter path:")
        if not os.path.isdir(path):
            print("Invalid directory.")

    dir_path = sys.argv[1] if len(sys.argv) > 1 else path
    prefix = sys.argv[2] if len(sys.argv) > 2 else 'Episode'

    rename_episodes(dir_path, prefix)

    print("Done.")
    input("Press Enter to exit...")

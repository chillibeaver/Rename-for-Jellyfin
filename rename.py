import os
import re
import sys


def extract_episode_number(filename):
    """从文件名中提取集数，返回 (集数, 匹配优先级) 或 None"""
    name = os.path.splitext(filename)[0]

    # 按优先级排列的匹配规则 (越靠前优先级越高)
    patterns = [
        # === 高优先级：明确的剧集标记 ===
        # S01E01, S1E1, s01e01
        (r'[Ss](\d+)[Ee](\d+)', lambda m: int(m.group(2)), 100),

        # EP01, Ep.01, Ep 01, EP.01
        (r'[Ee][Pp][\s._-]?(\d+)', lambda m: int(m.group(1)), 95),

        # Episode 01, Episode.01
        (r'[Ee]pisode[\s._-]?(\d+)', lambda m: int(m.group(1)), 95),

        # E01 (单独的E+数字，前后不能是字母)
        (r'(?<![A-Za-z])[Ee](\d+)(?![A-Za-z])', lambda m: int(m.group(1)), 90),

        # 第01集, 第01话, 第1集
        (r'第\s*(\d+)\s*[集话話]', lambda m: int(m.group(1)), 90),

        # 第一集 (中文数字)
        (r'第([一二三四五六七八九十百千]+)[集话話]', lambda m: cn_to_num(m.group(1)), 90),

        # === 中优先级：常见格式 ===
        # - 01 - 或 - 01. 或 - 01 [ (横杠分隔)
        (r'-\s*(\d{1,3})\s*(?:[-.\[\(]|$)', lambda m: int(m.group(1)), 80),

        # [01] 或 【01】(方括号内纯数字)
        (r'[\[【](\d{1,3})[\]】]', lambda m: int(m.group(1)), 75),

        # [01 (37)] 或 [01(37)] 格式 - 取第一个数字
        (r'[\[【](\d{1,3})\s*\(\d+\)\s*[\]】]', lambda m: int(m.group(1)), 85),

        # [01v2] [01V2] 带版本号
        (r'[\[【](\d{1,3})[vV]\d[\]】]', lambda m: int(m.group(1)), 85),

        # #01, #1
        (r'#(\d+)', lambda m: int(m.group(1)), 75),

        # 1x01, 1X01 (季x集格式)
        (r'(\d+)[xX](\d+)', lambda m: int(m.group(2)), 75),

        # Vol.01, Vol 01, Volume 01
        (r'[Vv]ol(?:ume)?[\s._-]?(\d+)', lambda m: int(m.group(1)), 70),

        # Part 01, Pt.01, Pt 01
        (r'[Pp](?:ar)?t[\s._-]?(\d+)', lambda m: int(m.group(1)), 70),

        # OVA01, OAD01, ONA01, SP01
        (r'(?:OVA|OAD|ONA|SP|PV)[\s._-]?(\d+)', lambda m: int(m.group(1)), 70),

        # Film 01, Movie 01
        (r'(?:Film|Movie)[\s._-]?(\d+)', lambda m: int(m.group(1)), 65),

        # === 低优先级：位置推断 ===
        # .01. 或 _01_ 或 空格01空格 (被分隔符包围)
        (r'[\s._\-](\d{2,3})[\s._\-]', lambda m: int(m.group(1)), 50),

        # 末尾的数字 (文件名结尾)
        (r'[\s._\-](\d{1,3})$', lambda m: int(m.group(1)), 40),

        # 开头的数字 (文件名开头)
        (r'^(\d{1,3})[\s._\-]', lambda m: int(m.group(1)), 40),

        # 最后的独立数字 (兜底)
        (r'(?:^|[^\d])(\d{1,3})(?:[^\d]|$)', lambda m: int(m.group(1)), 20),
    ]

    best_match = None
    best_priority = -1

    for pattern, extractor, priority in patterns:
        matches = list(re.finditer(pattern, name))
        if matches:
            # 对于低优先级模式，取最后一个匹配；高优先级取第一个
            match = matches[-1] if priority < 50 else matches[0]
            ep_num = extractor(match)

            # 过滤明显不是集数的数字 (年份、分辨率等)
            if is_likely_episode(ep_num, name, match):
                if priority > best_priority:
                    best_priority = priority
                    best_match = ep_num

    return best_match


def cn_to_num(cn_str):
    """中文数字转阿拉伯数字"""
    cn_nums = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
               '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
               '百': 100, '千': 1000, '零': 0}
    if cn_str == '十':
        return 10
    result = 0
    temp = 0
    for char in cn_str:
        if char in '十百千':
            if temp == 0:
                temp = 1
            result += temp * cn_nums[char]
            temp = 0
        else:
            temp = cn_nums.get(char, 0)
    result += temp
    return result if result > 0 else None


def is_likely_episode(num, filename, match):
    """判断数字是否可能是集数"""
    if num is None or num <= 0 or num > 999:
        return False

    # 获取匹配位置前后的上下文
    start, end = match.span()
    context_before = filename[max(0, start-10):start].lower()
    context_after = filename[end:end+10].lower()
    matched_text = match.group(0)

    # 排除年份 (1900-2099)
    if 1900 <= num <= 2099:
        # 但如果有明确标记就保留
        if re.search(r'[Ee]p?|第|[Ss]\d+[Ee]', matched_text, re.I):
            return True
        # 检查是否在方括号内且可能是集数格式
        if re.search(r'[\[【]\d{1,3}', matched_text):
            return True
        return False

    # 排除分辨率
    if num in [240, 360, 480, 540, 576, 720, 1080, 1440, 2160, 4320]:
        if re.search(r'[pi]|[×x]\d', context_after):
            return False

    # 排除比特率/码率
    if context_after.startswith(('kbps', 'mbps', 'k', 'mb')):
        return False

    # 排除版本号 (如果不在方括号格式中)
    if 'v' in context_before[-2:].lower() and num < 10:
        if not re.search(r'[\[【]', context_before):
            return False

    return True


def check_conflict(new_name, path, current_file):
    """检查文件名冲突"""
    if new_name == current_file:
        return None
    new_path = os.path.join(path, new_name)
    if os.path.exists(new_path):
        return new_path
    return None


def rename_episodes(path='.', prefix='Episode', dry_run=False):
    """识别并重命名剧集文件"""
    video_exts = {'.mp4', '.mkv', '.avi', '.wmv', '.flv', '.mov',
                  '.rmvb', '.rm', '.m4v', '.ts', '.webm', '.m2ts'}
    subtitle_exts = {'.srt', '.ass', '.ssa',
                     '.sub', '.idx', '.vtt', '.sup', '.smi'}

    files = sorted(os.listdir(path))
    results = []

    # 第一遍：处理视频文件，记录重命名映射
    rename_map = {}  # {旧文件名(无扩展名): 新文件名(无扩展名)}

    for file in files:
        filepath = os.path.join(path, file)
        if not os.path.isfile(filepath):
            continue

        name, ext = os.path.splitext(file)

        if ext.lower() not in video_exts:
            continue

        ep_num = extract_episode_number(file)

        if ep_num is not None:
            new_base = f"{prefix} {ep_num:02d}"
            new_name = f"{new_base}{ext}"
            conflict = check_conflict(new_name, path, file)

            if conflict:
                results.append(('conflict', file, new_name))
            elif file != new_name:
                results.append(('rename', file, new_name, ep_num))
                rename_map[name] = new_base
            else:
                results.append(('skip', file, '已是目标格式'))
        else:
            results.append(('fail', file, '未识别到集数'))

    # 第二遍：处理字幕文件 (跟随视频或独立识别)
    for file in files:
        filepath = os.path.join(path, file)
        if not os.path.isfile(filepath):
            continue

        name, ext = os.path.splitext(file)
        if ext.lower() not in subtitle_exts:
            continue

        # 处理多后缀字幕: video.zh-Hans.ass, video.chs.srt
        base_name = name
        lang_suffix = ''
        for lang in ['.zh-hans', '.zh-hant', '.chs', '.cht', '.sc', '.tc',
                     '.zh', '.en', '.ja', '.jp', '.ko', '.chi', '.eng', '.jpn']:
            if name.lower().endswith(lang):
                base_name = name[:-len(lang)]
                lang_suffix = name[-len(lang):]
                break

        # 优先匹配已有视频的重命名
        matched = False
        for old_video_name, new_base in rename_map.items():
            if base_name == old_video_name or base_name.startswith(old_video_name + '.'):
                new_name = f"{new_base}{lang_suffix}{ext}"
                if file != new_name and not check_conflict(new_name, path, file):
                    results.append(('rename_sub', file, new_name))
                    matched = True
                break

        # 未匹配到视频时，独立识别字幕集数
        if not matched:
            ep_num = extract_episode_number(file)
            if ep_num is not None:
                new_name = f"{prefix} {ep_num:02d}{lang_suffix}{ext}"
                if file != new_name and not check_conflict(new_name, path, file):
                    results.append(('rename_sub', file, new_name))

    # 显示预览
    print(f"\n{'='*60}")
    print(f"目录: {os.path.abspath(path)}")
    print(f"前缀: {prefix}")
    print(f"{'='*60}\n")

    rename_count = 0
    for result in results:
        if result[0] == 'rename':
            print(f"  ✓ [视频] {result[1]}\n         → {result[2]}")
            rename_count += 1
        elif result[0] == 'rename_sub':
            print(f"  ✓ [字幕] {result[1]}\n         → {result[2]}")
            rename_count += 1
        elif result[0] == 'conflict':
            print(f"  ⚠ {result[1]}\n    → {result[2]} (冲突!)")
        elif result[0] == 'fail':
            print(f"  ✗ {result[1]} ({result[2]})")

    if rename_count == 0:
        print("  没有需要重命名的文件。")
        return 0

    if dry_run:
        print(f"\n[预览模式] 将重命名 {rename_count} 个文件")
        return rename_count

    # 确认执行
    print(f"\n将重命名 {rename_count} 个文件。")

    confirm = input("确认执行? (y/N): ").strip().lower()

    if confirm == 'n':
        print("已取消。")
        return 0

    # 执行重命名
    success = 0
    for result in results:
        if result[0] in ('rename', 'rename_sub'):
            old_path = os.path.join(path, result[1])
            new_path = os.path.join(path, result[2])
            try:
                os.rename(old_path, new_path)
                success += 1
            except Exception as e:
                print(f"  ✗ 重命名失败: {result[1]} - {e}")

    print(f"\n完成! 成功重命名 {success}/{rename_count} 个文件。")
    return success


def main():
    print("\n" + "="*60)
    print("       剧集批量重命名工具 v2.0")
    print("="*60)

    while True:
        print("\n" + "-"*40)

        # 获取目录
        if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
            path = sys.argv[1]
            sys.argv.pop(1)  # 用完就移除
        else:
            path = input("输入目录路径 (或 q 退出): ").strip()
            if path.lower() == 'q':
                print("再见!")
                break
            # 处理拖拽路径可能带引号的情况
            path = path.strip('"\'')

        if not os.path.isdir(path):
            print(f"✗ 无效目录: {path}")
            continue

        # 前缀
        prefix = 'Episode'

        # 执行重命名
        rename_episodes(path, prefix)


if __name__ == "__main__":
    main()

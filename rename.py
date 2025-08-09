import os
import re

VIDEO_FORMATS = {
    ".mp4": 1,
    ".avi": 1,
    ".mkv": 1,
    ".mov": 1,
    ".wmv": 1,
    ".flv": 1,
    ".webm": 1,
    ".mpeg": 1,
    ".mpg": 1,
    ".3gp": 1,
    ".rmvb": 1,
    ".ts": 1
}

SUB_FORMATS = {
    ".srt": 1,
    ".ass": 1,
    ".ssa": 1,
    ".vtt": 1,
    ".smi": 1,
    ".sub": 1,
    ".sup": 1
}

def match_pattern(filename, name, ext, dir_path, stats):
    print(f"  Checking: {filename}")
    pattern = r'\[(\d{1,2}(?:[vV]\d*)?)\]'
    match = re.search(pattern, name)
    
    if match:
        # Extract just the numeric part before any "v" or "V"
        episode_str = match.group(1)
        # Split by 'v' or 'V' and take the first part (the episode number)
        episode_num = re.split('[vV]', episode_str)[0]
        episode = str(int(episode_num))
        # Create new filename: episode number + original extension
        new_name = episode + ext
        old_path = os.path.join(dir_path, filename)
        new_path = os.path.join(dir_path, new_name)
        
        try:
            os.rename(old_path, new_path)
            print(f'    ✓ Renamed: "{filename}" → "{new_name}"')
            stats['renamed'].append((filename, new_name))
            return True
        except OSError as e:
            print(f'    ✗ Error: {e}')
            stats['failed'].append(filename)
            return False
    else:
        print(f'    - Pattern not matched')
        stats['skipped'].append(filename)
        return False

def rename_episode(filename, dir_path, stats):
    # Split filename and extension
    name, ext = os.path.splitext(filename)
    
    if ext in SUB_FORMATS:
        if ".sc" in name:
            stats['processed'] += 1
            return match_pattern(filename, name, ext, dir_path, stats)
        else:
            stats['skipped'].append(filename)
            return False
    
    if ext in VIDEO_FORMATS:
        stats['processed'] += 1
        return match_pattern(filename, name, ext, dir_path, stats)
    
    stats['skipped'].append(filename)
    return False

def main():

    print("=" * 60)
    
    dir_path = input('Enter directory path: ')
    dir_path = dir_path.replace("\\", "/")
    
    # Statistics
    stats = {
        'total': 0,
        'processed': 0,
        'renamed': [],
        'failed': [],
        'skipped': []
    }
    
    print("-" * 60)
    
    # Get all files
    try:
        files = os.listdir(dir_path)
        stats['total'] = len(files)
    except OSError as e:
        print(f"Error: Cannot access directory - {e}")
        return
    
    # Process each file
    for filename in files:
        rename_episode(filename, dir_path, stats)
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total files found:     {stats['total']}")
    print(f"Files processed:       {stats['processed']}")
    print(f"Successfully renamed:  {len(stats['renamed'])}")
    print(f"Failed to rename:      {len(stats['failed'])}")
    print(f"Skipped (no match):    {len(stats['skipped'])}")
    
    # Show renamed files if any
    if stats['renamed']:
        print("\n" + "-" * 60)
        print("Renamed files:")
        # Sort by the episode number (extract number from new filename)
        sorted_renamed = sorted(stats['renamed'], 
                              key=lambda x: int(os.path.splitext(x[1])[0]))
        for old, new in sorted_renamed:
            print(f"  {old} → {new}")
    
    # Show failed files if any
    if stats['failed']:
        print("\n" + "-" * 60)
        print("Failed to rename:")
        for filename in stats['failed']:
            print(f"  {filename}")
    
    print("\n" + "=" * 60)
    print("Process completed!")

if __name__ == "__main__":
    main()

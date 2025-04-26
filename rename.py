import os
import re
from tqdm import tqdm

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


def match_pattern(filename, name, ext, dir_path):
    print("\ncall match_pattern, current name: ", filename)
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
            print(f'Renamed "{filename}" to "{new_name}"')
        except OSError as e:
            print(f'Error renaming "{filename}": {e}')
    else:
        print(f'{filename} not match pattern')


def rename_episode(filename, dir_path):
    # Split filename and extension

    name, ext = os.path.splitext(filename)

    if ext in SUB_FORMATS:

        if ".sc" in name:
            match_pattern(filename, name, ext, dir_path)
            return

    if ext in VIDEO_FORMATS:
        match_pattern(filename, name, ext, dir_path)
        return


def main():

    dir_path = input('Enter directory path: ')
    dir_path = dir_path.replace("\\", "/")

    for filename in tqdm(os.listdir(dir_path)):
        rename_episode(filename, dir_path)


if __name__ == "__main__":
    main()

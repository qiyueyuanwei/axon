from pathlib import Path
from typing import List

def video_files_in(dirpath: Path) -> List[Path]:
        exts = {".mp4", ".mov", ".mkv", ".avi", ".ts", ".mpg", ".mpeg", ".flv"}
        if not dirpath.exists():
                return []
        return sorted([p for p in dirpath.iterdir() if p.suffix.lower() in exts and p.is_file()])
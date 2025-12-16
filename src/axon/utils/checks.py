import shutil
# import logging
import sys
from axon.utils.cpu import CPUInfo


def ensure_ffmpeg_available():
        if str(CPUInfo()) == "None":
                # print(str(CPUInfo()))
                print("cpu info has not been found!!!!")
        else:
                print(CPUInfo.name())
        if shutil.which("ffmpeg") is None:
                print("ffmpeg 未找到，请先安装 ffmpeg 并确保在 PATH 中可用。")
                sys.exit(2)
import argparse
import logging
import os
import signal
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import List
from axon.utils import ensure_ffmpeg_available,video_files_in


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
axon run: 在 data/videos 中查找视频并向指定 RTSP 服务器推流
用法示例:
    python run.py --host localhost --port 8554 --app live --copy --loop
默认会使用 libx264/aac 转码；如果指定 --copy 则尝试直接拷贝编码（更省资源，但并非所有文件/容器都支持）
"""


# --- 配置日志 ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("axon.run")


def find_project_root(start: Path) -> Path:
        """向上查找含 pyproject.toml 或 README.md 或 .git 的项目根目录，找不到则返回 start.parent"""
        cur = start.resolve()
        for _ in range(8):
                if (cur / "pyproject.toml").exists() or (cur / "README.md").exists() or (cur / ".git").exists():
                        return cur
                if cur.parent == cur:
                        break
                cur = cur.parent
        return start.parent


# def video_files_in(dirpath: Path) -> List[Path]:
#         exts = {".mp4", ".mov", ".mkv", ".avi", ".ts", ".mpg", ".mpeg", ".flv"}
#         if not dirpath.exists():
#                 return []
#         return sorted([p for p in dirpath.iterdir() if p.suffix.lower() in exts and p.is_file()])


def build_ffmpeg_cmd(src: Path, rtsp_url: str, copy: bool, loop: bool) -> List[str]:
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "warning"]
        if loop:
                # -stream_loop -1 表示无限循环输入（注意：对某些格式无效）
                cmd += ["-stream_loop", "-1"]
        cmd += ["-re", "-i", str(src)]
        if copy:
                cmd += ["-c", "copy"]
        else:
                # 低延迟实时转码设置
                cmd += ["-c:v", "libx264", "-preset", "veryfast", "-tune", "zerolatency", "-c:a", "aac", "-ar", "44100"]
        # 推送为 RTSP
        # 使用短超时时间并尽量保持连接
        cmd += ["-f", "rtsp", "-rtsp_transport", "tcp", rtsp_url]
        return cmd


def start_streams(videos: List[Path], host: str, port: int, app: str, copy: bool, loop: bool):
        procs = {}
        for vid in videos:
                stream_name = vid.stem
                rtsp_url = f"rtsp://{host}:{port}/{app}/{stream_name}"
                cmd = build_ffmpeg_cmd(vid, rtsp_url, copy, loop)
                logger.info("启动推流: %s -> %s", vid.name, rtsp_url)
                logger.debug("ffmpeg cmd: %s", " ".join(cmd))
                try:
                        p = subprocess.Popen(cmd)
                        procs[vid] = (p, rtsp_url)
                except Exception as e:
                        logger.error("无法启动 ffmpeg 推流 %s: %s", vid, e)

        # 注册终止处理
        def _terminate(signum, frame):
                logger.info("收到终止信号，停止所有推流...")
                for v, (p, url) in procs.items():
                        if p.poll() is None:
                                logger.info("终止: %s <- %s", v.name, url)
                                try:
                                        p.terminate()
                                except Exception:
                                        pass
                # 等待短时间然后强杀
                time.sleep(1.0)
                for v, (p, url) in procs.items():
                        if p.poll() is None:
                                try:
                                        p.kill()
                                except Exception:
                                        pass
                sys.exit(0)

        signal.signal(signal.SIGINT, _terminate)
        signal.signal(signal.SIGTERM, _terminate)

        # 监控子进程，若任何退出则记录
        try:
                while True:
                        all_dead = True
                        for v, (p, url) in list(procs.items()):
                                ret = p.poll()
                                if ret is None:
                                        all_dead = False
                                else:
                                        logger.warning("推流进程退出: %s 退出码=%s url=%s", v.name, ret, url)
                                        # 不自动重启，保留记录
                                        procs.pop(v, None)
                        if not procs:
                                logger.info("没有活动推流进程，退出")
                                break
                        time.sleep(1.0)
        except KeyboardInterrupt:
                _terminate(None, None)


# def ensure_ffmpeg_available():
#         if shutil.which("ffmpeg") is None:
#                 logger.error("ffmpeg 未找到，请先安装 ffmpeg 并确保在 PATH 中可用。")
#                 sys.exit(2)


def main(argv=None):
        from cfg.parser import args

        if args.verbose:
                logger.setLevel(logging.DEBUG)

        here = Path(__file__).resolve()
        project_root = Path(args.root) if args.root else find_project_root(here)
        logger.debug("项目根目录: %s", project_root)

        data_videos = project_root / "data" / "videos"
        if not data_videos.exists():
                logger.info("创建目录: %s", data_videos)
                try:
                        data_videos.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                        logger.error("无法创建 data/videos 目录: %s", e)
                        sys.exit(1)

        videos = video_files_in(data_videos)
        if not videos:
                logger.warning("未在 %s 中发现视频文件。请将视频放入该目录后重新运行。", data_videos)
                sys.exit(0)

        ensure_ffmpeg_available()
        start_streams(videos, args.host, args.port, args.app, args.copy, args.loop)


if __name__ == "__main__":
        main()
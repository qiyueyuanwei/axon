import argparse

parser = argparse.ArgumentParser(description="axon - 将 data/videos 中的视频推送为 RTSP 流")
parser.add_argument("--host", default="localhost", help="RTSP 服务器主机 (默认: localhost)")
parser.add_argument("--port", default=8554, type=int, help="RTSP 服务器端口 (默认: 8554)")
parser.add_argument("--app", default="live", help="RTSP 流应用路径 (默认: live) -> rtsp://host:port/app/streamname")
parser.add_argument("--copy", action="store_true", help="尝试直接拷贝编码流 (更省资源，但不总是可用)")
parser.add_argument("--loop", default=True,action="store_true", help="循环播放视频")
parser.add_argument("--root", default=None, help="项目根目录（可选），默认自动识别 pyproject.toml 所在目录")
parser.add_argument("--verbose", action="store_true", help="显示调试信息")
args = parser.parse_args()


if __name__ == "__main__":
    args_dict = vars(args)
    print(f"args is {args_dict}")
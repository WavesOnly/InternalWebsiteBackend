from cv2 import VideoCapture, CAP_PROP_FPS, imwrite
from os.path import join
from tempfile import TemporaryDirectory
from shutil import copyfileobj
from io import BytesIO


class Screenshot:
    def __init__(self):
        pass

    def capture(self, video: bytes, timestamp: str = "00:00:02") -> object:
        with TemporaryDirectory() as directory:
            path = join(directory, "video.mp4")
            with open(path, "wb") as buffer:
                with BytesIO(video) as stream:
                    copyfileobj(stream, buffer)
            capture = VideoCapture(path)
            fps = capture.get(CAP_PROP_FPS)
            timestamps = [float(time) for time in timestamp.split(":")]
            hours, minutes, seconds = timestamps
            frame = (hours * 3600 * fps) + (minutes * 60 * fps) + (seconds * fps)
            capture.set(1, frame)
            success, frame = capture.read()
            if not success:
                raise RuntimeError(f"Failed to read the frame at timestamp {timestamp}")
            return frame

    def save(self, frame: object, directory: TemporaryDirectory, filename: str = "Thumbnail.jpg") -> None:
        path = join(directory, filename)
        success = imwrite(path, frame)
        if not success:
            raise RuntimeError("Failed to save the frame to a temporary file.")
        return path

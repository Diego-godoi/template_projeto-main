from enum import Enum


class FileType(str, Enum):
    Application = "application"
    Image = "image"
    Text = "text"
    Video = "video"

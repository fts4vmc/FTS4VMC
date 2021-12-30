import os
class Config(object):
    DEBUG = False
    TESTING = False
    UPLOAD_FOLDER = os.path.relpath("uploads")
    TMP_FOLDER = os.path.join("src",'static','tmp')
    VMC_LINUX = os.path.relpath('vmc65-linux')
    VMC_MAC = os.path.relpath('vmc-macos')
    VMC_WINDOWS = os.path.relpath('vmc-win7.exe')
#Maximum uploaded file size 1MB
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024

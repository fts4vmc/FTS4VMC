import os
class Config(object):
    DEBUG = False
    TESTING = False
#Path to the folder used for storing uploaded files
    UPLOAD_FOLDER = os.path.relpath("uploads")
#Path to the folder used for storing temporary files
    TMP_FOLDER = os.path.join("src",'static','tmp')
#Path to the VMC binaries
    VMC_LINUX = os.path.relpath('vmc65-linux')
    VMC_MAC = os.path.relpath('vmc-macos')
    VMC_WINDOWS = os.path.relpath('vmc-win7.exe')
#Maximum uploaded file size 1MB
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
#Maximum number of edges for rendering graph using dot
    RENDER_GRAPH_EDGE_LIMIT = 300
#Define the direction used to render dot graphs
#Accepted value are: TB, BT, LR, RL
    RENDER_GRAPH_DIRECTION = 'TB'

import os

# 当前节点的UUID
NODE_ID = os.environ.get('V2RAY_NODE_ID', 'set_your_node_id_here')

# 请求v2rayui需要用到的API Key
API_KEY = os.environ.get('V2RAY_NODE_API_KEY', 'set_your_api_key_here')

# v2rayui的API请求地址
V2RAYUI_URL = 'https://example.com'

# 向v2rayui获取新用户的时间间隔，单位：秒
CHECK_USER_INTERVAL = 60

# 向v2rayui上传流量信息的时间间隔，单位：秒
UPDATE_TRAFFIC_INTERVAL = 600

# v2ray的gRPC API通信地址
V2RAY_API_HOST = '127.0.0.1'

# v2ray的gRPC API通信端口
V2RAY_API_PORT = 1234

# v2ray的inbound tag
V2RAY_INBOUND_TAG = 'master'

# v2ray_agent
v2rayui配置v2ray的agent代理端，与v2ray一同运行在服务器上，使得v2rayui支持管理多个v2ray服务器。需结合v2rayui使用。

# 特点
1. 基于v2ray_api对v2ray进行增加或移除用户而无须重启v2ray进程，注：仅支持VMESS协议增减用户。感谢[spencer404](https://github.com/spencer404)用户开发的v2ray Python API [v2ray_api](https://github.com/spencer404/v2ray_api)

2. 同时对v2ray的config.json配置文件增减用户，使得v2ray重启后可以通过config.json配置文件立即加载用户配置。

3. 支持获取每个用户的使用流量，并定期上报到v2rayui。

# 使用
现在就自己使用而已，不想写文档。。。^-^

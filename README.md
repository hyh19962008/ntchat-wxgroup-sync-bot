# ntchat-wxgroup-sync-bot
基于ntchat的微信群聊同步机器人  

微信群有500人上限的限制，建立多个群的话又有信息无法互通的不便，此机器人通过自动将消息转发到同一个同步组内的所有群，消除这一不便性，间接达成扩大群成员数的目的。目前支持文本、图片、表情、视频、链接、文件、引用、小程序、视频号、位置、批量聊天记录11种类型的消息。
## 特别提醒
> 使用机器人有被封禁微信账号的风险，请尽量注册小号来运行，本人对因使用本机器人造成账号封禁带来的损失不负责任。
## 隐私声明
本程序运行过程中所产生的数据、文件均保存在用户本地，不向任何第三方发送。
## 运行环境
- python 3.6+
- [微信PC客户端 3.6.0.18](https://github.com/tom-snow/wechat-windows-versions/releases/download/v3.6.0.18/WeChatSetup-3.6.0.18.exe)
## 安装依赖
`pip install ntchat`  
`pip install python-magic python-magic-bin`
## 运行
1. 正常登录PC微信（不要使用脚本登录，容易被封）
2. 执行脚本注入微信，加-l参数获取群列表  
`python main.py -l`  
3. 第一次运行会打印出所有的微信群名及其对应的wxid，然后退出
4. 将需要同步的群的wxid填入groups.json中的room_id中，name推荐使用简短一些的名称如"XX 1群"
5. 再次执行脚本  
`python main.py`  
## 示例
![chat1](https://raw.githubusercontent.com/hyh19962008/ntchat-wxgroup-sync-bot/main/example/chat1.png)
![chat2](https://raw.githubusercontent.com/hyh19962008/ntchat-wxgroup-sync-bot/main/example/chat2.png)
## 已知问题
- 暂不支持同步消息撤回
- sub_type=40 的批量转发消息没有正文（没有加载到本地）
- 视频超过一定大小时(大概20MB)，微信不会自动下载，无法触发机器人的动作
- 在微信没有重启的情况下，多次重新执行脚本容易引起微信崩溃
## 捐赠
- 支付宝: hyh19962008@gmail.com
## 致谢
- [ntchat](https://github.com/billyplus/ntchat)
- [wechat-windows-versions](https://github.com/tom-snow/wechat-windows-versions) 保存微信历史版本 
# ntchat-wxgroup-sync-bot
基于ntchat的微信群聊同步机器人  

微信群有500人上限的限制，建立多个群的话又有信息无法互通的不便，此机器人通过自动将消息转发到同一个同步组内的所有群，消除这一不便性，间接达成扩大群成员数的目的。目前支持文本、图片、表情、链接、文件5种类型的消息。
## 特别提醒
> 使用机器人有被封禁微信账号的风险，请尽量注册小号来运行，本人对因使用本机器人造成账号封禁带来的损失不负责任。
## 运行环境
- python 3.6+
- [微信PC客户端 3.6.0.18](https://github.com/tom-snow/wechat-windows-versions/releases/download/v3.6.0.18/WeChatSetup-3.6.0.18.exe)
## 安装依赖
`pip install ntchat`
`pip install python-magic python-magic-bin`
## 运行
1. 正常登录PC微信（不要使用脚本登录，容易被封）
2. 执行脚本注入微信  
`python main.py`  
3. 第一次运行会打印出所有的微信群名及其对应的wxid，然后退出
4. 将需要同步的微信群名和wxid填入sync_groups中，并注释掉"获取群列表并输出"部分代码
5. 再次执行脚本
`python main.py`  
## 致谢
- [ntchat](https://github.com/billyplus/ntchat)
- [wechat-windows-versions](https://github.com/tom-snow/wechat-windows-versions) 保存微信历史版本 
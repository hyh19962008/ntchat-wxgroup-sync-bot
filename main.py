# -*- coding: utf-8 -*-
import sys
import os
import ntchat
import time
import random
from xml.etree import ElementTree as ET
import urllib.request
import magic    # pip3 install python-magic python-magic-bin
import copy


# 所有同步组，第一维数组的每个元素为一个同步组，一个同步组内有多个群聊
# name是转发到其他群时显示的标题
# member_list是wxid到用户名的dict
# 可使用下方的“获取群列表”部分代码获取wxid
sync_groups = [
    [
        {"name": "工作1群", "room_id": "01234567@chatroom", "member_list" : {}}, 
        {"name": "工作2群", "room_id": "012345678@chatroom", "member_list" : {}}
    ],
    [
        {"name": "同学1群", "room_id": "123456789@chatroom", "member_list" : {}}, 
        {"name": "同学2群", "room_id": "1234567890@chatroom", "member_list" : {}}
    ]
]

wxid_to_group_index_map = {}
room_wxid_to_room_index_map = {}
my_wxid = ''

# 用户自定义 工作目录
WorkDir = "D:/wechat_bot/"

#################################################

wechat = ntchat.WeChat()

# 打开pc微信, smart: 是否管理已经登录的微信
wechat.open(smart=True)

# 等待登录
wechat.wait_login()

# 获取自己的wxid
info = wechat.get_self_info()
my_wxid = info["wxid"]

if not os.path.exists(WorkDir + "/emoji"):
    try:
        os.makedirs(WorkDir + "/emoji")
    except:
        print("无法在工作目录" + WorkDir + "建立文件夹， 请检查是否拥有写入权限，或者修改工作目录路径")
        exit(-1)

# 获取群列表并输出
rooms = wechat.get_rooms()
for r in rooms:
    print(f'群聊名: {r["nickname"]}, wxid: {r["wxid"]}, 成员数: {r["total_member"]}')
time.sleep(3)
ntchat.exit_()
sys.exit()

# picture sending control
class LastSender():
    def __init__(self):
        self.wxid = ""
        self.time = 0.0
        self.msg_type = 0

last_sender = LastSender()

# 建立 wxid/room_id 到sync_group数组下标的映射
for i in range(len(sync_groups)):
    for room in sync_groups[i]:
        room_id = room["room_id"]
        wxid_to_group_index_map[room_id] = i

# 建立 "room_id + _ + wxid" 到sync_group[i]数组下标的映射
for group in sync_groups:
    for j in range(len(group)):
        room = group[j]
        room_id = room["room_id"]
        member_list = room["member_list"]

        data = wechat.get_room_members(room_id)
        for member in data["member_list"]:
            wxid = member["wxid"]
            key1 = room_id + "_" + wxid
            if member["display_name"]:
                member_list[wxid] = member["display_name"]
            else:
                member_list[wxid] = member["nickname"]
            room_wxid_to_room_index_map[key1] = j

        # 随机延迟1-5s，避免频率过于频繁
        delay = random.randint(1, 5)
        time.sleep(delay)
        

# 获取xml标签的内容
def extractXmlText(inXml, head, tail):
    start = inXml.find(head)
    end1 = inXml.find(tail)
    sub = inXml[start + len(head) : end1]
    return sub

# 获取xml tag的值
def extractXmlTag(inXml, tagName):
    p1 = inXml.find(tagName)
    p2 = inXml.find('"', p1)
    p3 = inXml.find('"', p2+1)
    return inXml[p2+1 : p3]

# 下载表情文件并返回路径
def get_emoji_file(xmlContent):
    root = ET.XML(xmlContent)
    emoji = root.find("emoji")
    url = emoji.get("cdnurl")
    filename = emoji.get("md5")

    # 将表情下载到emoji文件夹下
    path = "emoji/" + filename
    if not os.path.exists(path):
        urllib.request.urlretrieve(url, path)
        exist = False
    else:
        exist = True

    return path

# 替换link中的fromusername为自己
def update_link_fromuser(xmlContent):
    wxid = extractXmlText(xmlContent, "<fromusername>", "</fromusername>")
    xmlContent = xmlContent.replace(wxid, my_wxid)
    return xmlContent

# 更新某个群聊的成员列表
def update_member_list(room_id):
    i = wxid_to_group_index_map[room_id]
    group = sync_groups[i]

    for j in range(len(group)):
        room = group[j]
        _room_id = room["room_id"]
        if room_id == _room_id:
            member_list = room["member_list"]
            member_list.clear()

            data = wechat.get_room_members(room_id)
            for member in data["member_list"]:
                wxid = member["wxid"]
                key1 = room_id + "_" + wxid
                if member["display_name"]:
                    member_list[wxid] = member["display_name"]
                else:
                    member_list[wxid] = member["nickname"]
                room_wxid_to_room_index_map[key1] = j
            break

# 查找某个群聊中的用户名称
def get_group_member_name(room_id, wxid):
    key1 = room_id + "_" + wxid
    i = wxid_to_group_index_map[room_id]
    j = room_wxid_to_room_index_map.get(key1)

    # 查找miss时更新成员列表
    if j == None:
        update_member_list(room_id)
        j = room_wxid_to_room_index_map.get(key1)
        if j == None:
            return "None"

    name = sync_groups[i][j]["member_list"][wxid]
    if not name:
        name = "None"

    return name

# 返回群聊名
def get_room_name(room_id):
    i = wxid_to_group_index_map.get(room_id)
    for room in sync_groups[i]:
        if room_id == room["room_id"]:
            return room["name"]

# 返回需要同步消息的群聊组
def get_sync_group_list(room_id):
    i = wxid_to_group_index_map.get(room_id)
    if i == None:
        return None
    else:
        return sync_groups[i]


# 通用的回调处理，封装成函数修饰器
def main_handle_wrapper(action):
    def inner(wechat_instance: ntchat.WeChat, message):
        data = message["data"]
        from_wxid = data["from_wxid"]
        room_wxid = data["room_wxid"]
        delay = random.randint(1, 5)

        if from_wxid != my_wxid:
            group = get_sync_group_list(room_wxid)
            if group:
                room_name = get_room_name(room_wxid)
                name = get_group_member_name(room_wxid, from_wxid)
                
                # 遍历同步组中的所有群聊
                for room in group:
                    if room["room_id"] != room_wxid:
                        # 随机延迟1-5s，避免频率过于频繁
                        time.sleep(delay)
                        return action(wechat_instance=wechat_instance, data=data,
                                       room_name=room_name, name=name, room=room)
    
    return inner



# 文本消息处理动作
@main_handle_wrapper
def text_action(wechat_instance: ntchat.WeChat, data, room_name, name, room):
    last_sender.msg_type = ntchat.MT_RECV_TEXT_MSG
    
    for user in data['at_user_list']:
        # 被@时回复提示消息, @所有人时不回复
        if user == my_wxid and data['msg'].find("@所有人") == -1:
            # 只发送一次(因为group内有2个以上的群时text_action触发多次)
            try:
                if data['_robot_prompted']:
                    pass
            except:
                wechat_instance.send_text(to_wxid=data["room_wxid"], content="你好我是机器人叮咚，我负责在不同群之间同步转发消息，实现互联互通。")
                data['_robot_prompted'] = True
    print("send to : " + room["name"] + room["room_id"])
    wechat_instance.send_text(to_wxid=room["room_id"], content=f"{room_name}-{name}:\n----------\n{data['msg']}")

# 注册文本消息回调
@wechat.msg_register(ntchat.MT_RECV_TEXT_MSG)
def on_recv_text_msg2(wechat_instance: ntchat.WeChat, message):
    text_action(wechat_instance, message)



# 图片消息处理动作
@main_handle_wrapper
def pic_action(wechat_instance: ntchat.WeChat, data, room_name, name, room):
    pic1 = data['image']
    xmlContent = data["raw_msg"]
    root = ET.XML(xmlContent)
    img1 = root.find("img")
    length1 = img1.get("length") or img1.get("hdlength")    # 两个标签之一有可能为空
    pic1_size = int(length1)

    # 等待图片完整下载到本地
    while not os.path.exists(pic1):
        time.sleep(0.5)
    while os.path.getsize(pic1) < pic1_size:
        time.sleep(0.5)

    # 如果在30秒内连续发送图片，则不再附加发送者信息的标题
    cur_time = time.time()
    if last_sender.wxid != data["from_wxid"] or (cur_time - last_sender.time > 30) or last_sender.msg_type != ntchat.MT_RECV_IMAGE_MSG:
        wechat_instance.send_text(to_wxid=room["room_id"], content=f"{room_name}-{name}:")
    last_sender.wxid = data["from_wxid"]
    last_sender.time = cur_time
    last_sender.msg_type = ntchat.MT_RECV_IMAGE_MSG
    time.sleep(0.2)
    wechat_instance.send_image(room["room_id"], data['image'])

# 注册图片消息回调
@wechat.msg_register(ntchat.MT_RECV_IMAGE_MSG)
def on_recv_image_msg(wechat_instance: ntchat.WeChat, message):
    pic_action(wechat_instance, message)



# 表情消息处理动作
@main_handle_wrapper
def emoji_action(wechat_instance: ntchat.WeChat, data, room_name, name, room):
    # 先将表情文件下载到本地，然后作为图片或gif发送
    file = get_emoji_file(data['raw_msg'])
    mime = magic.from_file(file, True)

    # 如果在30秒内连续发送，则不再附加发送者信息的标题
    cur_time = time.time()
    if last_sender.wxid != data["from_wxid"] or (cur_time - last_sender.time > 30) or last_sender.msg_type != ntchat.MT_RECV_EMOJI_MSG:
        wechat_instance.send_text(to_wxid=room["room_id"], content=f"{room_name}-{name}:")
    last_sender.wxid = data["from_wxid"]
    last_sender.time = cur_time
    last_sender.msg_type = ntchat.MT_RECV_EMOJI_MSG
    time.sleep(0.2)
    if mime == "image/png" or mime == "image/jpeg":
        wechat_instance.send_image(room["room_id"], WorkDir + file)
    elif mime == "image/gif":
        wechat_instance.send_gif(room["room_id"], WorkDir + file)

# 注册表情消息回调
@wechat.msg_register(ntchat.MT_RECV_EMOJI_MSG)
def on_recv_emoji_msg(wechat_instance: ntchat.WeChat, message):
    emoji_action(wechat_instance, message)



# 链接消息处理动作
@main_handle_wrapper
def link_action(wechat_instance: ntchat.WeChat, data, room_name, name, room):
    last_sender.msg_type = ntchat.MT_RECV_LINK_MSG
    wechat_instance.send_text(to_wxid=room["room_id"], content=f"{room_name}-{name}:")
    time.sleep(0.2)
    data['raw_msg'] = update_link_fromuser(data['raw_msg'])
    wechat_instance.send_xml(room["room_id"], data['raw_msg'])

# 注册链接消息回调
@wechat.msg_register(ntchat.MT_RECV_LINK_MSG)
def on_recv_link_msg(wechat_instance: ntchat.WeChat, message):
    link_action(wechat_instance, message)



# 文件消息处理动作
@main_handle_wrapper
def file_action(wechat_instance: ntchat.WeChat, data, room_name, name, room):
    # 如果在30秒内连续发送，则不再附加发送者信息的标题
    cur_time = time.time()
    if last_sender.wxid != data["from_wxid"] or (cur_time - last_sender.time > 30) or last_sender.msg_type != ntchat.MT_RECV_FILE_MSG:
        wechat_instance.send_text(to_wxid=room["room_id"], content=f"{room_name}-{name}:")
    last_sender.wxid = data["from_wxid"]
    last_sender.time = cur_time
    last_sender.msg_type = ntchat.MT_RECV_FILE_MSG
    time.sleep(0.2)
    wechat_instance.send_file(room["room_id"], data['file'])

# 注册文件消息回调
@wechat.msg_register(ntchat.MT_RECV_FILE_MSG)
def on_recv_file_msg(wechat_instance: ntchat.WeChat, message):
    file_action(wechat_instance, message)



# 引用消息处理动作 
@main_handle_wrapper
def reference_action(wechat_instance: ntchat.WeChat, data, room_name, name, room):
    last_sender.msg_type = ntchat.MT_RECV_OTHER_APP_MSG
    xmlContent = data["raw_msg"]
    root = ET.XML(xmlContent)
    appmsg = root.find("appmsg")
    msg = appmsg.find("title")
    
    refermsg = appmsg.find("refermsg")
    reftype = refermsg.find("type")
    reftype = int(reftype.text)
    refname = refermsg.find("displayname")
    refmsg = refermsg.find("content")
    refwxid = refermsg.find("chatusr")
    
    # 文字
    if reftype == 1:
        # 内容太长截短
        startp = refmsg.text.find("----------\n") 
        startp += 1
        if startp > 0:
            startp += len("----------\n")
        if len(refmsg.text[startp:]) > 37:
            refmsg.text = refmsg.text[0:36+startp] + "..."
        # 被引用消息是机器人转发的消息，不附加发送者(机器人)标题
        if refwxid.text == my_wxid:
            if refmsg.text.find("\n") == 0:
                refmsg.text = refmsg.text.replace("\n", "", 1)
            wechat_instance.send_text(to_wxid=room["room_id"], content=f"{room_name}-{name}:\n----------\n{msg.text}\n#引用\n{refmsg.text}")
        else:
            wechat_instance.send_text(to_wxid=room["room_id"], content=f"{room_name}-{name}:\n----------\n{msg.text}\n#引用\n{refname.text}: {refmsg.text}")
    # 图片
    elif reftype == 3:
        wechat_instance.send_text(to_wxid=room["room_id"], content=f"{room_name}-{name}:\n----------\n{msg.text}\n#引用\n{refname.text}: 图片")
    # 表情
    elif reftype == 47:
        wechat_instance.send_text(to_wxid=room["room_id"], content=f"{room_name}-{name}:\n----------\n{msg.text}\n#引用\n{refname.text}: 表情")
    # 链接/文件
    elif reftype == 49:
        content = refmsg.text
        newroot = ET.fromstring(content)
        appmsg2 = newroot.find("appmsg")
        link_type = int(appmsg2.find("type").text)
        link_title = appmsg2.find("title").text

        if link_type == 5:
            wechat_instance.send_text(to_wxid=room["room_id"], content=f"{room_name}-{name}:\n----------\n{msg.text}\n#引用\n{refname.text}: 链接={link_title}")
        elif link_type == 6:
            wechat_instance.send_text(to_wxid=room["room_id"], content=f"{room_name}-{name}:\n----------\n{msg.text}\n#引用\n{refname.text}: 文件={link_title}")
        # 57=对另一个文字的引用, 53=含 #话题 的文字/接龙?
        elif link_type == 57 or link_type == 53:
            wechat_instance.send_text(to_wxid=room["room_id"], content=f"{room_name}-{name}:\n----------\n{msg.text}\n#引用\n{refname.text}: {link_title}")
        else:
            wechat_instance.send_text(to_wxid=room["room_id"], content=f"{room_name}-{name}:\n----------\n{msg.text}\n#引用\n{refname.text}: 链接=NULL")
    # 其他
    else:
        wechat_instance.send_text(to_wxid=room["room_id"], content=f"{room_name}-{name}:\n----------\n{msg.text}\n#引用\n{refname.text}: 未知消息")

# 视频号消息处理动作
@main_handle_wrapper
def video_finder_action(wechat_instance: ntchat.WeChat, data, room_name, name, room):
    last_sender.msg_type = ntchat.MT_RECV_OTHER_APP_MSG
    wechat_instance.send_text(to_wxid=room["room_id"], content=f"{room_name}-{name}:")
    time.sleep(0.2)
    data['raw_msg'] = update_link_fromuser(data['raw_msg'])
    wechat_instance.send_xml(room["room_id"], data['raw_msg'])

# 注册其他应用消息回调
@wechat.msg_register(ntchat.MT_RECV_OTHER_APP_MSG)
def on_recv_other_app_msg(wechat_instance: ntchat.WeChat, message):
    if message["data"]["wx_type"] == 49:
        # QQ音乐
        if message["data"]["wx_sub_type"] == 3:
            video_finder_action(wechat_instance, message)
        # 动画表情
        if message["data"]["wx_sub_type"] == 8:
            video_finder_action(wechat_instance, message)
        # 引用消息
        elif message["data"]["wx_sub_type"] == 57:
            reference_action(wechat_instance, message)
        # 视频号
        elif message["data"]["wx_sub_type"] == 51:
            video_finder_action(wechat_instance, message)



# 小程序消息处理动作
@main_handle_wrapper
def miniapp_action(wechat_instance: ntchat.WeChat, data, room_name, name, room):
    last_sender.msg_type = ntchat.MT_RECV_MINIAPP_MSG
    wechat_instance.send_text(to_wxid=room["room_id"], content=f"{room_name}-{name}:")
    time.sleep(0.2)
    data['raw_msg'] = update_link_fromuser(data['raw_msg'])
    wechat_instance.send_xml(room["room_id"], data['raw_msg'])

# 注册小程序消息回调
@wechat.msg_register(ntchat.MT_RECV_MINIAPP_MSG)
def on_recv_miniapp_msg(wechat_instance: ntchat.WeChat, message):
    miniapp_action(wechat_instance, message)



# 视频消息处理动作
@main_handle_wrapper
def video_action(wechat_instance: ntchat.WeChat, data, room_name, name, room):
    last_sender.msg_type = ntchat.MT_RECV_VIDEO_MSG
    wechat_instance.send_text(to_wxid=room["room_id"], content=f"{room_name}-{name}:")
    time.sleep(0.2)
    wechat_instance.send_video(room["room_id"], data['video'])

# 注册视频消息回调
@wechat.msg_register(ntchat.MT_RECV_VIDEO_MSG)
def on_recv_video_msg(wechat_instance: ntchat.WeChat, message):
    video_action(wechat_instance, message)



# 位置消息处理动作
@main_handle_wrapper
def location_action(wechat_instance: ntchat.WeChat, data, room_name, name, room):
    last_sender.msg_type = ntchat.MT_RECV_LOCATION_MSG
    root = ET.XML(data['raw_msg'])
    location = root.find("location")
    point1 = location.get("poiname")
    label1 = location.get("label")
    wechat_instance.send_text(to_wxid=room["room_id"], content=f"{room_name}-{name}:\n[位置] {point1}\n{label1}")

# 注册位置消息回调
@wechat.msg_register(ntchat.MT_RECV_LOCATION_MSG)
def on_recv_location_msg(wechat_instance: ntchat.WeChat, message):
    location_action(wechat_instance, message)



# @wechat.msg_register(ntchat.MT_ALL)
# def on_recv_text_msg(wechat_instance: ntchat.WeChat, message):
#     data = message["data"]
#     from_wxid = data["from_wxid"]
#     room_wxid = data["room_wxid"]
#     delay = random.randint(1, 5)    
#     time.sleep(delay)
#     print(data)


# 主循环
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    ntchat.exit_()
    sys.exit()
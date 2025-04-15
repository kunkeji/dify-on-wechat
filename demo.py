import ntwork
import time
import json
import os
import signal
import sys
from typing import List, Dict, Union

class WeWorkBot:
    def __init__(self, smart: bool = True):
        """
        初始化企业微信机器人
        :param smart: 是否使用智能模式
        """
        self.wework = ntwork.WeWork()
        self.smart = smart
        self.login_info = None
        self.rooms = {}  # 群聊缓存
        self.contacts = {}  # 联系人缓存
        self.running = False  # 运行状态标志
        
    def start(self):
        """启动机器人"""
        # 打开企业微信
        if not self.wework.open(self.smart):
            print("打开企业微信失败")
            return False
            
        # 等待登录
        print("等待登录...")
        self.wework.wait_login()
        
        # 获取登录信息
        self.login_info = self.wework.get_login_info()
        print(f"登录成功，用户名: {self.login_info['username']}")
        
        # 注册消息处理函数
        self._register_handlers()
        
        # 初始化缓存
        self._init_cache()
        
        # 设置运行状态
        self.running = True
        
        return True
        
    def stop(self):
        """停止机器人"""
        if self.running:
            print("正在关闭机器人...")
            self.running = False
            # 关闭企业微信
            self.wework.close()
            print("机器人已关闭")
            
    def _register_handlers(self):
        """注册所有消息处理函数"""
        # 文本消息
        @self.wework.msg_register(ntwork.MT_RECV_TEXT_MSG)
        def text_handler(wework_instance, message):
            if self.running:  # 只在运行状态下处理消息
                self._handle_text_message(message)
            
        # 图片消息
        @self.wework.msg_register(ntwork.MT_RECV_IMAGE_MSG)
        def image_handler(wework_instance, message):
            if self.running:
                self._handle_image_message(message)
            
        # 文件消息
        @self.wework.msg_register(ntwork.MT_RECV_FILE_MSG)
        def file_handler(wework_instance, message):
            if self.running:
                self._handle_file_message(message)
            
        # 语音消息
        @self.wework.msg_register(ntwork.MT_RECV_VOICE_MSG)
        def voice_handler(wework_instance, message):
            if self.running:
                self._handle_voice_message(message)
            
        # 链接消息
        @self.wework.msg_register(ntwork.MT_RECV_LINK_CARD_MSG)
        def link_handler(wework_instance, message):
            if self.running:
                self._handle_link_message(message)
            
        # 群成员变动消息
        @self.wework.msg_register(11072)
        def room_member_change_handler(wework_instance, message):
            if self.running:
                self._handle_room_member_change(message)
            
    def _init_cache(self):
        """初始化缓存数据"""
        # 获取群聊列表
        self.rooms = self._get_rooms()
        
        # 获取联系人列表
        self.contacts = self._get_contacts()
        
        # 获取群成员信息
        self._update_room_members()
        
    def _get_rooms(self, page_num: int = 1, page_size: int = 500) -> Dict:
        """
        获取群聊列表
        :param page_num: 页码
        :param page_size: 每页数量
        :return: 群聊列表
        """
        rooms = self.wework.get_rooms(page_num, page_size)
        if rooms and isinstance(rooms, dict) and 'room_list' in rooms:
            return {room['conversation_id']: room for room in rooms['room_list']}
        return {}
        
    def _get_contacts(self, page_num: int = 1, page_size: int = 500) -> Dict:
        """
        获取联系人列表
        :param page_num: 页码
        :param page_size: 每页数量
        :return: 联系人列表
        """
        contacts = self.wework.get_external_contacts(page_num, page_size)
        if contacts and isinstance(contacts, dict) and 'contact_list' in contacts:
            return {contact['user_id']: contact for contact in contacts['contact_list']}
        return {}
        
    def _update_room_members(self):
        """更新所有群的成员信息"""
        for room_id in self.rooms:
            members = self.wework.get_room_members(room_id)
            if members and isinstance(members, dict) and 'member_list' in members:
                self.rooms[room_id]['members'] = members['member_list']
                
    def _handle_text_message(self, message: Dict):
        """处理文本消息"""
        data = message.get('data', {})
        sender = data.get('sender')
        content = data.get('content', '')
        conversation_id = data.get('conversation_id')
        
        # 判断是否为群聊消息
        is_group = "R:" in conversation_id
        if sender == self.login_info['user_id']:
            return  # 如果是自己发送的消息，直接返回不处理
        
        print(f"收到{'群聊' if is_group else '私聊'}消息:")
        print(f"发送者: {sender}")
        print(f"内容: {content}")
        
        # 示例：自动回复
        if not is_group:
            self.send_text(conversation_id, f"收到消息: {content}")
            
    def _handle_image_message(self, message: Dict):
        """处理图片消息"""
        data = message.get('data', {})
        cdn = data.get("cdn")
        file_id = cdn.get('file_id')
        aes_key = cdn.get('aes_key')
        file_size = cdn.get('file_size')
        
        # 下载图片
        save_path = f"downloads/{file_id}.jpg"
        self.wework.c2c_cdn_download(file_id, aes_key, file_size, 3, save_path)
        
    def _handle_file_message(self, message: Dict):
        """处理文件消息"""
        data = message.get('data', {})
        file_id = data.get('file_id')
        aes_key = data.get('aes_key')
        file_size = data.get('file_size')
        file_name = data.get('file_name')
        
        # 下载文件
        save_path = f"downloads/{file_name}"
        self.wework.c2c_cdn_download(file_id, aes_key, file_size, 4, save_path)
        
    def _handle_voice_message(self, message: Dict):
        """处理语音消息"""
        data = message.get('data', {})
        cdn = data.get('cdn')
        file_id = cdn.get('file_id')
        aes_key = cdn.get('aes_key')
        file_size = cdn.get('file_size')
        
        # 下载语音
        save_path = f"downloads/{file_id}.silk"
        self.wework.c2c_cdn_download(file_id, aes_key, file_size, 34, save_path)
        
    def _handle_link_message(self, message: Dict):
        """处理链接消息"""
        data = message.get('data', {})
        cdn = data.get('cdn')
        title = cdn.get('title')
        desc = cdn.get('desc')
        url = cdn.get('url')
        
        print(f"收到链接消息:")
        print(f"标题: {title}")
        print(f"描述: {desc}")
        print(f"链接: {url}")
        
    def _handle_room_member_change(self, message: Dict):
        """处理群成员变动消息"""
        data = message.get('data', {})
        member_list = data.get('member_list', [])
        conversation_id = data.get('conversation_id')
        
        for member in member_list:
            user_id = member['user_id']
            name = member['name']
            print(f"群成员变动: {name}({user_id})")
            
        # 更新群成员缓存
        self._update_room_members()
        
    # 消息发送方法
    def send_text(self, conversation_id: str, content: str) -> bool:
        """
        发送文本消息
        :param conversation_id: 会话ID
        :param content: 消息内容
        :return: 是否发送成功
        """
        return self.wework.send_text(conversation_id, content)
        
    def send_image(self, conversation_id: str, file_path: str) -> bool:
        """
        发送图片消息
        :param conversation_id: 会话ID
        :param file_path: 图片文件路径
        :return: 是否发送成功
        """
        return self.wework.send_image(conversation_id, file_path)
        
    def send_file(self, conversation_id: str, file_path: str) -> bool:
        """
        发送文件消息
        :param conversation_id: 会话ID
        :param file_path: 文件路径
        :return: 是否发送成功
        """
        return self.wework.send_file(conversation_id, file_path)
        
    def send_video(self, conversation_id: str, file_path: str) -> bool:
        """
        发送视频消息
        :param conversation_id: 会话ID
        :param file_path: 视频文件路径
        :return: 是否发送成功
        """
        return self.wework.send_video(conversation_id, file_path)
        
    def send_room_at_msg(self, conversation_id: str, content: str, at_list: List[str]) -> bool:
        """
        发送群@消息
        :param conversation_id: 群ID
        :param content: 消息内容
        :param at_list: @的用户ID列表
        :return: 是否发送成功
        """
        return self.wework.send_room_at_msg(conversation_id, content, at_list)
        
    def send_link_card(self, conversation_id: str, title: str, desc: str, url: str, image_url: str) -> bool:
        """
        发送链接卡片消息
        :param conversation_id: 会话ID
        :param title: 标题
        :param desc: 描述
        :param url: 链接地址
        :param image_url: 图片地址
        :return: 是否发送成功
        """
        return self.wework.send_link_card(conversation_id, title, desc, url, image_url)
        
    def send_card(self, conversation_id: str, user_id: str) -> bool:
        """
        发送名片消息
        :param conversation_id: 会话ID
        :param user_id: 用户ID
        :return: 是否发送成功
        """
        return self.wework.send_card(conversation_id, user_id)
        
    def get_contact_detail(self, user_id: str) -> Dict:
        """
        获取联系人详细信息
        :param user_id: 用户ID
        :return: 联系人信息
        """
        return self.wework.get_contact_detail(user_id)
        
    def get_room_members(self, conversation_id: str, page_num: int = 1, page_size: int = 500) -> Dict:
        """
        获取群成员列表
        :param conversation_id: 群ID
        :param page_num: 页码
        :param page_size: 每页数量
        :return: 群成员列表
        """
        return self.wework.get_room_members(conversation_id, page_num, page_size)

# 使用示例
if __name__ == "__main__":
    # 创建机器人实例
    bot = WeWorkBot(smart=True)
    
    # 注册信号处理
    def signal_handler(sig, frame):
        print("\n检测到Ctrl+C，正在退出...")
        bot.stop()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # 启动机器人
        if bot.start():
            print("机器人启动成功")
            print("按Ctrl+C退出程序")
            
            # 保持程序运行
            while bot.running:
                time.sleep(1)
    except Exception as e:
        print(f"发生错误: {e}")
        bot.stop()
        sys.exit(1)
from time import sleep
from tkinter import *
import tkinter.font as TkFont
import threading
from g_python.gextension import Extension
from g_python.hpacket import HPacket
from g_python.hmessage import Direction, HMessage
from g_python.hparsers import HEntity, HEntityType

extension_info = {
    "title": "G-Friends",
    "description": "Application to add friends",
    "author": "denio4321",
    "version": "1.0"
}

GREEN = "#75BD4B"
RED = "#FF0000"
WHITE = "#FFF"


class HFriends:
    def __init__(self, packet):
        self.friends = []
        _, _ = packet.read('ii')
        self.total_friends = packet.read_int()
        for _ in range(self.total_friends):
            id_user, name, _, _, _, clothes, _, motto, _, _, _, _, _, _ = packet.read('isiBBsisssBBBu')
            self.friends.append([id_user, name, clothes, motto])


class Friendbomber:
    def __init__(self, extension: Extension):
        global GREEN, RED, WHITE
        self.__ext = extension
        self.TOTAL_ADDS = 0
        self.ACTIVE = False
        self.friend_list = []
        self.root = Tk()
        self.root.iconphoto(False, PhotoImage(file='icon.png'))
        self.text_font = TkFont.Font(family="System", size=10)
        self.root.option_add('System', '10')
        self.root.title("G-Friends")
        self.root.geometry("250x400")
        self.root.resizable(False, False)
        self.main_frame = Frame(self.root, width=250, height=100)
        self.main_frame.pack()
        self.status_label = Label(self.main_frame, text="Status: Inactive", fg=RED, font=self.text_font)
        self.status_label.grid(row=0, column=0, pady=15, sticky=N)
        self.total_adds = Label(self.main_frame, text=f"Total adds: {self.TOTAL_ADDS}", font=self.text_font)
        self.total_adds.grid(row=0, column=0, pady=35, sticky=S)
        self.total_friends = Label(self.main_frame, text="Friend list: Not loaded yet.", font=self.text_font)
        self.total_friends.grid(row=0, column=0, pady=15, sticky=S)
        self.start_button = Button(self.main_frame, text="Start", font=self.text_font, command=self.activate,
                                   bg=WHITE, width=10)
        self.start_button.grid(row=1, column=0, pady=10, padx=15, sticky=W)
        self.load_friends = Button(self.main_frame, text="Load Friends", font=self.text_font,
                                   command=self.request_friends,
                                   bg=WHITE, width=10)
        self.load_friends.grid(row=1, column=0, pady=10, padx=15, sticky=E)
        self.root.attributes('-topmost', True)
        self.log_box = Text(self.main_frame, state=DISABLED, width=20, height=5)
        self.scrollbar = Scrollbar(self.main_frame, command=self.log_box.yview, orient="vertical")
        self.scrollbar.grid(row=3, column=1, sticky="ns")
        self.log_box.grid(row=3, column=0, ipady=50, ipadx=30)
        self.message_box = Entry(self.main_frame, width=35)
        self.message_box.grid(row=4, column=0, pady=10, padx=7)
        self.send_message_btn = Button(self.main_frame, text="Send", font=self.text_font, command=self.send_msg_btn,
                                       bg=WHITE, width=10)
        self.send_message_btn.grid(row=5, column=0, padx=20)

        ext.intercept(Direction.TO_CLIENT, self.clear_log, 'RoomReady')
        ext.intercept(Direction.TO_CLIENT, self.obtain_friend_list, 'FriendListFragment')
        ext.intercept(Direction.TO_CLIENT, self.start_adding, 'Users', mode="async")
        ext.intercept(Direction.TO_CLIENT, self.block_err, 'MessengerError')

        ext.on_event('connection_end', self.exit_extension)

        self.root.mainloop()

    @staticmethod
    def exit_extension():
        exit()

    def clear_log(self, message):
        self.log_box.configure(state='normal')
        self.log_box.delete("1.0", END)
        self.log_box.configure(state='disabled')

    def send_msg_btn(self):
        threading.Thread(target=self.send_message).start()

    def send_message(self):
        if self.friend_list:
            for friend_entity in self.friend_list.friends:
                user_id = friend_entity[0]
                user_name = friend_entity[1]
                if "{user}" in self.message_box.get():
                    message = self.message_box.get().replace("{user}", user_name)
                else:
                    message = self.message_box.get()
                ext.send_to_server(HPacket('SendMsg', user_id, message))
                sleep(0.5)
            self.log_box.configure(state='normal')
            self.log_box.insert(END,
                                f"[G-Friends] Succesfully messaged all of your friends!\n")
            self.log_box.see(END)
            self.log_box.configure(state='disabled')
        else:
            self.log_box.configure(state='normal')
            self.log_box.insert(END,
                                f"Load first your friends!\n")
            self.log_box.see(END)
            self.log_box.configure(state='disabled')

    @staticmethod
    def request_friends():
        ext.send_to_server(HPacket('MessengerInit'))

    def obtain_friend_list(self, message: HMessage):
        self.friend_list = HFriends(message.packet)
        self.log_box.configure(state='normal')
        self.log_box.insert(END,
                            f"[G-Friends] Added {self.friend_list.total_friends} friends to the friend list!\n")
        self.log_box.see(END)
        self.log_box.configure(state='disabled')
        self.total_friends.configure(text=f"Loaded Friends: {self.friend_list.total_friends}")
        message.is_blocked = True

    def start_adding(self, message: HMessage):
        global GREEN, RED, WHITE
        if self.ACTIVE:
            packet = message.packet
            entities = HEntity.parse(packet)
            for entity in entities:
                if entity.entity_type == HEntityType.HABBO:
                    self.__ext.send_to_server(HPacket('RequestFriend', str(entity.name)))
                    self.TOTAL_ADDS += 1
                    self.total_adds.configure(text=f"Total adds: {self.TOTAL_ADDS}")
                    self.log_box.configure(state='normal')
                    self.log_box.insert(END,
                                        f"Adding {entity.name}\n")
                    self.log_box.see(END)
                    self.log_box.configure(state='disabled')

                    sleep(1)

    def activate(self):
        global GREEN

        self.ACTIVE = True
        self.status_label.configure(text="Status: Active", fg=GREEN)
        self.start_button.configure(bg=GREEN, text="Stop", command=self.deactivate)

    def deactivate(self):
        global RED, WHITE
        self.status_label.configure(text="Status: Inactive", fg=RED)
        self.start_button.configure(bg=WHITE, text="Start", command=self.activate)
        self.ACTIVE = False

    @staticmethod
    def block_err(message: HMessage):
        message.is_blocked = True


ext = Extension(extension_info, args=sys.argv)
ext.start()

g_friends = Friendbomber(ext)

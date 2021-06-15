import sys
from time import sleep
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

ext = Extension(extension_info, args=sys.argv)
ext.start()

TOTAL_ADDS = 0

def start_adding(message):
    global TOTAL_ADDS
    packet = message.packet
    entities = HEntity.parse(packet)
    for entity in entities:
        if entity.entity_type == HEntityType.HABBO:
            ext.send_to_server(HPacket('RequestFriend', str(entity.name)))
            TOTAL_ADDS += 1
            print(f"[G-Friends] Adding {entity.name}, Total friends added {TOTAL_ADDS}")
            sleep(1)

def BlockMsgErr(message : HMessage):
    message.is_blocked = True

ext.intercept(Direction.TO_CLIENT, start_adding, 'Users', mode='async')
ext.intercept(Direction.TO_CLIENT, BlockMsgErr, 'MessengerError')
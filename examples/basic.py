from kmbox_universal import HidKey, KMBoxClient


client = KMBoxClient("192.168.2.188", 6314, "39EBDC32")
client.key_press(HidKey.C, 60)
client.move(120, 0)
client.click("left")

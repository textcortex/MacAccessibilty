from textCortex.mac_accessible import MacAccessbility


def call_back(notificatio, data):
    print(f"notification {notificatio} data {data}")


mac = MacAccessbility(call_back)

mac.start()
c

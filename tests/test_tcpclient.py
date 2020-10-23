from pantools.TCPClient import TCPClient

def test_constructor():
    tcp = TCPClient("Magic", 7777)

def test_connect():
    tcp = TCPClient("Magic", 7777)
    tcp.connect_to_service("localhost",5678)
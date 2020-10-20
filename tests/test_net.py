from os import wait
import pantools.net as pt

def test_ip():
    str = pt.get_local_ip()
    pt.announce_service("MAGICCOOKIE",9999, "0.0.0.0", 6969)
    # pt.wait_for_announcement(9999, "MAGICCOOKIE")

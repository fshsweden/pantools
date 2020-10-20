from pantools.net import haversine
def test_haversine():
    assert haversine(52.370216, 4.895168, 52.520008,13.404954) == 945793.4375088713


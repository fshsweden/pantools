import pickle

def to_network_packet(json):
    m = pickle.dumps(json)
    return m
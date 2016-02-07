from lib.Bencoder import Bencoder
from lib.Tracker import Tracker

from lib.Tracker import announce_udp
import itertools
import hashlib
import bencode

import urllib
import urllib2



__author__ = 'User'


if __name__ == '__main__':

    decoded = Bencoder().decode(r'.\content\torrents\The Great Book Of Best Quotes Of All Time By Abhi Sharma.torrent')
    encoded = Bencoder().encode(decoded["info"])

    print("something")

    h = hashlib.new('sha1')
    h.update(encoded)
    info_hash = h.hexdigest()

    info, peers = Tracker().announce(decoded["announce-list"], info_hash, 100000,0,0 )


    for p in peers:
        print "IP: {} Port: {}".format(p["IP"], p["port"])

    print(info_hash)


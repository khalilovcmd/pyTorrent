import lib.Bencoder
import lib.Tracker
import hashlib
import bencode

import urllib
import urllib2



__author__ = 'User'


if __name__ == '__main__':

    torrent = lib.Bencoder.read()

    # bytes = []
    # pieces = torrent['info']['pieces']
    #
    # for num in range(0, 20):
    #     bytes.append(pieces[num])
    #
    # hash = ''.join('{:02x}'.format(x) for x in pieces)
    #


    print(torrent)

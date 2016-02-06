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

    info_hash_file = open(r'E:\Trial-Code\BitTorrent\torrents\info_dicitonary.txt', 'rb')

    text = info_hash_file.read()

    print(len(text))

    info_hash_file.close()

    h = hashlib.new('sha1')
    h.update(text)
    info_hash =  h.hexdigest()

    print(info_hash)

    info_hash = urllib.quote(info_hash)

    print(info_hash)


    torrent_file = open(r'E:\Trial-Code\BitTorrent\torrents\[kat.cr]the.intern.2015.hdrip.xvid.ac3.evo.torrent', 'rb')
    metainfo = bencode.bdecode(torrent_file.read())
    info = metainfo['info']
    info_encode = bencode.bencode(info)
    sha = hashlib.sha1(info_encode).digest()
    info_hash =  urllib.quote_plus(sha)

    print info_hash


    bd = bencode.bdecode(urllib2.urlopen("http://mgtracker.org:2710/announce?info_hash=%A0pL6%F9Dx%1624%3B%87%90%EB%EBe%2FW%9A%C2&peer_id=ABCZZZZ11J6034OPQRST&ip=94.201.200.169&port=19002&downloaded=200&left=10000000&event=started&numwant=250").read())

    v = lib.Tracker.announce_udp("udp://tracker.openbittorrent.com:80",
                                 { "info_hash" : "09FCC9A201F432D6EEF508C11896493CEE342FFA", "downloaded": "1000", "uploaded": "1000000", "left": "500000000", "peer_id" : "953245GHIJKL3865QRSTDASDSAD" })

    print v
    print(torrent)

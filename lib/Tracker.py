import binascii
import socket
import random
import struct
import itertools

from Base import Base

from urlparse import urlparse

class Tracker(Base):

    def __init__(self):
        super(Tracker, self).__init__()
        pass

    def announce(self, announce_list, info_hash, left, downloaded = 0, uploaded =0 ):

        tracker_urls = self.__flatten_list(announce_list)

        for url in tracker_urls:
            try:

                # parse hostname and port of the tracker_url
                hostname, port = self.__get_tracker_info(url)

                # initialize the socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(10)

                # initialize address
                address = (socket.gethostbyname(hostname), port)

                # 1. connection to tracker

                # create connection request
                req, conn_transaction_id = self.__create_connection_request()

                # send req to tracker
                sock.sendto(req, address)

                # receive res from tracker
                connection_request_buf = sock.recvfrom(2048)[0]

                # parse connection response and get connection_id
                connection_id = self.__parse_connection_response(connection_request_buf, conn_transaction_id)

                # 2. announce to tracker

                # create announce request
                req, ann_transaction_id = self.__create_announce_request(connection_id, info_hash, self.__get_peer_id(), port, left, downloaded, uploaded  )

                # send request to tracker
                sock.sendto(req, address)

                # receive res from tracker
                announce_request_buf = sock.recvfrom(2048)[0]

                # parse announce response and get announce result object
                return self.__parse_announce_response(announce_request_buf, ann_transaction_id)

            except Exception as ex:
                self.logger.info(ex.message)
                pass

    def __create_connection_request(self):

        action = 0x0                                    #action (0 = give me a new connection id)
        connection_id = 0x41727101980                   #default connection id
        transaction_id = self.__get_transaction_id()

        buf = struct.pack("!q", connection_id)          #first 8 bytes is connection id
        buf += struct.pack("!i", action)                #next 4 bytes is action
        buf += struct.pack("!i", transaction_id)        #next 4 bytes is transaction id

        return (buf, transaction_id)

    def __parse_connection_response(self, buf, sent_transaction_id):

        if len(buf) < 16:
            raise RuntimeError("Wrong response length getting connection id: %s" % len(buf))

        action = struct.unpack_from("!i", buf)[0] #first 4 bytes is action

        res_transaction_id = struct.unpack_from("!i", buf, 4)[0] #next 4 bytes is transaction id

        if res_transaction_id != sent_transaction_id:
            raise RuntimeError("Transaction ID doesnt match in connection response! Expected %s, got %s" % (sent_transaction_id, res_transaction_id))

        if action == 0x0:
            connection_id = struct.unpack_from("!q", buf, 8)[0] #unpack 8 bytes from byte 8, should be the connection_id
            return connection_id
        elif action == 0x3:
            error = struct.unpack_from("!s", buf, 8)
            raise RuntimeError("Error while trying to get a connection response: %s" % error)

        pass

    def __create_announce_request(self, connection_id, info_hash, peer_id, port, left, downloaded = 0, uploaded =0):

        action = 0x1                                                        #action (1 = announce)
        transaction_id = self.__get_transaction_id()

        buf = struct.pack("!q", connection_id)                              #first 8 bytes is connection id
        buf += struct.pack("!i", 0x1)                                       #next 4 bytes is action
        buf += struct.pack("!i", int(0))                                    #followed by 4 byte transaction id
        buf += struct.pack("!20s", binascii.unhexlify(info_hash))           #the info hash of the torrent we announce ourselves in
        buf += struct.pack("!20s", binascii.unhexlify(peer_id))             #the peer_id we announce
        buf += struct.pack("!q", int(0))                                    #number of bytes downloaded
        buf += struct.pack("!q", int(left))                                #number of bytes left
        buf += struct.pack("!q", int(0))                                    #number of bytes uploaded
        buf += struct.pack("!i", 0x2)                                       #event 2 denotes start of downloading
        buf += struct.pack("!I", 0x0)                                       #IP address set to 0. Response received to the sender of this packet
        key = udp_get_transaction_id()                                      #Unique key randomized by client
        buf += struct.pack("!I", key)
        buf += struct.pack("!i", -1)                                        #Number of peers required. Set to -1 for default
        buf += struct.pack("!H", port)                                      #port on which response will be sent


        return (buf, transaction_id)

    def __parse_announce_response(self, buf, sent_transaction_id):
        if len(buf) < 20:
            raise RuntimeError("Wrong response length while announcing: %s" % len(buf))
        action = struct.unpack_from("!i", buf)[0] #first 4 bytes is action

        res_transaction_id = struct.unpack_from("!i", buf, 4)[0] #next 4 bytes is transaction id
        # if res_transaction_id != sent_transaction_id:
        #     raise RuntimeError("Transaction ID doesnt match in announce response! Expected %s, got %s"
        #         % (sent_transaction_id, res_transaction_id))
        print "Reading Response"
        if action == 0x1:
            print "Action is 3"
            ret = dict()
            offset = 8; #next 4 bytes after action is transaction_id, so data doesnt start till byte 8
            ret['interval'] = struct.unpack_from("!i", buf, offset)[0]
            print "Interval:"+str(ret['interval'])
            offset += 4
            ret['leeches'] = struct.unpack_from("!i", buf, offset)[0]
            print "Leeches:"+str(ret['leeches'])
            offset += 4
            ret['seeds'] = struct.unpack_from("!i", buf, offset)[0]
            print "Seeds:"+str(ret['seeds'])
            offset += 4
            peers = list()
            x = 0
            while offset != len(buf):
                peers.append(dict())
                peers[x]['IP'] = struct.unpack_from("!i",buf,offset)[0]
                print "IP: "+socket.inet_ntoa(struct.pack("!i",peers[x]['IP']))
                offset += 4
                if offset >= len(buf):
                    raise RuntimeError("Error while reading peer port")
                peers[x]['port'] = struct.unpack_from("!H",buf,offset)[0]
                print "Port: "+str(peers[x]['port'])
                offset += 2
                x += 1
            return ret,peers
        else:
            #an error occured, try and extract the error string
            error = struct.unpack_from("!s", buf, 8)
            print "Action="+str(action)
            raise RuntimeError("Error while annoucing: %s" % error)

    def __get_tracker_info(self, tracker_url):

        tracker = tracker_url.lower()
        parsed = urlparse(tracker)

        url = parsed.geturl()[3:]
        url = "http" + url

        hostname = urlparse(url).hostname
        port = urlparse(url).port

        return (hostname, port)

    def __get_transaction_id(self):
        return int(random.randrange(0, 600000))

    def __get_peer_id(self):
        return ''.join(random.choice('0123456789abcdef') for n in xrange(40))

    def __flatten_list(self, value):

        return list(itertools.chain(*value))

import binascii, urllib, socket, random, struct
from bcode import bdecode
from binascii import unhexlify
import bencode
import array
import hashlib
from urlparse import urlparse, urlunsplit

def long_to_bytes(val, endianness='big'):
    """
    Use :ref:`string formatting` and :func:`~binascii.unhexlify` to
    convert ``val``, a :func:`long`, to a byte :func:`str`.

    :param long val: The value to pack

    :param str endianness: The endianness of the result. ``'big'`` for
      big-endian, ``'little'`` for little-endian.

    If you want byte- and word-ordering to differ, you're on your own.

    Using :ref:`string formatting` lets us use Python's C innards.
    """

    # one (1) hex digit per four (4) bits
    width = val.bit_length()

    # unhexlify wants an even multiple of eight (8) bits, but we don't
    # want more digits than we need (hence the ternary-ish 'or')
    width += 8 - ((width % 8) or 8)

    # format width specifier: four (4) bits per hex digit
    fmt = '%%0%dx' % (width // 4)

    # prepend zero (0) to the width, to zero-pad the output
    s = unhexlify(fmt % val)

    if endianness == 'little':
        # see http://stackoverflow.com/a/931095/309233
        s = s[::-1]

    return s

def announce_udp(tracker,payload):
    tracker = tracker.lower()
    parsed = urlparse(tracker)

    # Teporarly Change udp:// to http:// to get hostname and portnumbe
    url = parsed.geturl()[3:]
    url = "http" + url
    hostname = urlparse(url).hostname
    port = urlparse(url).port


    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(8)
    conn = (socket.gethostbyname(hostname), port)
    #sock.bind((socket.gethostname(),s_port))

    #Get connection ID
    req, transaction_id = udp_create_connection_request()
    sock.sendto(req, conn);
    buf = sock.recvfrom(2048)[0]
    connection_id = udp_parse_connection_response(buf, transaction_id)

    #Annoucing
    s_port = sock.getsockname()[1] #get port number to which socket is connected
    req, transaction_id = udp_create_announce_request(connection_id, payload,s_port)
    sock.sendto(req, conn)
    print "Announce Request Sent"
    
    buf = sock.recvfrom(2048)[0]
    print "Response received"
    
    return udp_parse_announce_response(buf, transaction_id)

def udp_create_announce_request(connection_id, payload, s_port):
    action = 0x1 #action (1 = announce)
    transaction_id = udp_get_transaction_id()
    # print "2.Transaction ID :", transaction_id
    print "announce request - connection_id: ", connection_id
    print "announce request - info_hash: ", urllib.unquote(payload['info_hash'])
    
    print "connection --> ", connection_id
    
    print "connection type --> ", type(connection_id)
    
    print "Length ->> ", len(urllib.unquote("09FCC9A201F432D6EEF508C11896493CEE342FFA"))
    
    buf = struct.pack("!q", connection_id)                                  #first 8 bytes is connection id
    buf += struct.pack("!i", 0x1)                                        #next 4 bytes is action 
    buf += struct.pack("!i", int(0))                                        #followed by 4 byte transaction id
    buf += struct.pack("!20s", binascii.unhexlify("09FCC9A201F432D6EEF508C11896493CEE342FFA"))        #the info hash of the torrent we announce ourselves in
    buf += struct.pack("!20s", binascii.unhexlify("2d5554333435302df0a26f95ad254bd3ba0ce85d"))          #the peer_id we announce
    buf += struct.pack("!q", int(0))    #number of bytes downloaded
    buf += struct.pack("!q", int(2882529379))          #number of bytes left
    buf += struct.pack("!q", int(0))      #number of bytes uploaded
    buf += struct.pack("!i", 0x2)                                           #event 2 denotes start of downloading
    buf += struct.pack("!I", 0x0)                                           #IP address set to 0. Response received to the sender of this packet
    key = udp_get_transaction_id()                                          #Unique key randomized by client
    buf += struct.pack("!I", 2666511055) 
    buf += struct.pack("!i", -1)                                            #Number of peers required. Set to -1 for default
    buf += struct.pack("!H", s_port)                                        #port on which response will be sent
    
    
    return (buf, transaction_id)

def udp_parse_announce_response(buf, sent_transaction_id):
    #print "Response is:"+str(buf)  
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

def udp_create_connection_request():
    connection_id = 0x41727101980                   #default connection id
    action = 0x0                                    #action (0 = give me a new connection id)   
    transaction_id = udp_get_transaction_id()
    print "1.Transaction ID :", transaction_id
    buf = struct.pack("!q", connection_id)          #first 8 bytes is connection id
    buf += struct.pack("!i", action)                #next 4 bytes is action
    buf += struct.pack("!i", transaction_id)        #next 4 bytes is transaction id
    
    return (buf, transaction_id)

def udp_parse_connection_response(buf, sent_transaction_id):
    if len(buf) < 16:
        raise RuntimeError("Wrong response length getting connection id: %s" % len(buf))            
    action = struct.unpack_from("!i", buf)[0] #first 4 bytes is action

    res_transaction_id = struct.unpack_from("!i", buf, 4)[0] #next 4 bytes is transaction id
    if res_transaction_id != sent_transaction_id:
        raise RuntimeError("Transaction ID doesnt match in connection response! Expected %s, got %s"
            % (sent_transaction_id, res_transaction_id))

    if action == 0x0:
        connection_id = struct.unpack_from("!q", buf, 8)[0] #unpack 8 bytes from byte 8, should be the connection_id
        
        print "1.connection_id ID :", connection_id
        return connection_id
    elif action == 0x3:     
        error = struct.unpack_from("!s", buf, 8)
        raise RuntimeError("Error while trying to get a connection response: %s" % error)
    pass

def udp_get_transaction_id():
    return int(random.randrange(0, 255))




def custom_udp_parse_announce_response(buf):
    #print "Response is:"+str(buf)  
    if len(buf) < 20:
        raise RuntimeError("Wrong response length while announcing: %s" % len(buf)) 
    action = struct.unpack_from("!i", buf)[0] #first 4 bytes is action
    res_transaction_id = struct.unpack_from("!i", buf, 4)[0] #next 4 bytes is transaction id    
    
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
	

def custom_udp_parse_announce_request(buf):
    
    print("request len: ", len(buf))

    offset = 0
    
    connection_id = struct.unpack_from("!q", buf, offset)[0] #next 8 bytes is connection_id
    
    offset += 8
    
    action = struct.unpack_from("!i", buf, offset)[0] #next 4 bytes is transaction_id
    
    offset += 4
    
    transaction_id = struct.unpack_from("!i", buf, offset)[0] #next 4 bytes is transaction_id
    
    offset += 4
    
    info_hash = struct.unpack_from("!20s", buf, offset)[0] #next 20 bytes is info_hash
    
    offset += 20
    
    peer_id = struct.unpack_from("!20s", buf, offset)[0] #next 20 bytes is peer_id
    
    offset += 20
    
    downloaded = struct.unpack_from("!q", buf, offset)[0] #next 8 bytes is downloaded
    
    offset += 8
    
    left = struct.unpack_from("!q", buf, offset)[0] #next 8 bytes is left
    
    offset += 8
    
    uploaded = struct.unpack_from("!q", buf, offset)[0] #next 8 bytes is uploaded
    
    offset += 8
    
    status = struct.unpack_from("!i", buf, offset)[0] #next 8 bytes is status (downloading) 
    
    offset += 4
    
    ip = struct.unpack_from("!I", buf, offset)[0] #next 4 bytes is ip-address
    
    offset += 4
    
    unique_key = struct.unpack_from("!I", buf, offset)[0] #next 4 bytes is unique-key
    
    offset += 4
    
    peers_num = struct.unpack_from("!i", buf, offset)[0] #next 4 bytes is no-peers
    
    offset += 4
    
    port = struct.unpack_from("!H", buf, offset)[0] #next 4 bytes is no-peers
    
    offset += 2
    
    # sum is: 98
    
    username_length = struct.unpack_from("!b", buf, offset)[0] #next 4 bytes is no-peers
    
    offset += 1
    
    username = struct.unpack_from("!2b", buf, offset)[0] #next 4 bytes is no-peers
    
    offset += 2
    
    hashing = struct.unpack_from("!8B", buf, offset)[0] #next 4 bytes is no-peers
    
    
    print("buffer length: ", len(buf))

    
    # hashing = struct.unpack_from("!8s", buf, offset)[0] #next 4 bytes is no-peers
    
    # offset += 8
    
    
    #username = struct.unpack_from("!"+str(length)+"s", buf, offset)[0] #next 4 bytes is no-peers
    
    #offset += length
    
    print(connection_id)
    print(action)
    print(transaction_id)
    print(binascii.hexlify(info_hash))
    print(binascii.hexlify(peer_id))
    print(downloaded)
    print(left)
    print(uploaded)
    print(status)
    print(ip)
    print(unique_key)
    print(peers_num)
    print(port)
    print(username_length)
    print(username)
    print(hashing)
    

if __name__ == '__main__':
    
    torrent = open("sample.torrent", 'rb')
    metainfo = bencode.bdecode(torrent.read())
    info = metainfo['info']
    
    info_decode = bencode.bencode(info)
    
    sha = hashlib.sha1(info_decode).hexdigest()
    
    print(sha)
    
    
    result = announce_udp("udp://tracker.openbittorrent.com:80/announce", { "info_hash": "09FCC9A201F432D6EEF508C11896493CEE342FFA", "peer_id": "2d5554333435302df0a26f95ad254bd3ba0ce85d", "downloaded": "0", "left":"2882529379", "uploaded": "0" })
    
    
    print(result)
    
    print("awesomely starting....")
    
    
    # opening wireshark response file
    udp_response_file = open("udp_announce_response.txt", 'rb')
    udp_response_hex_asbytes = udp_response_file.read()
    hex_data = udp_response_hex_asbytes.decode("hex")
    udp_response_bytes = array.array('B', hex_data)
    
    #result  = custom_udp_parse_announce_response(udp_response_bytes)

    # opening wireshark request file
    udp_request_file = open("udp_announce_request.txt", 'rb')
    udp_request_hex_asbytes = udp_request_file.read()
    res_hex_data = udp_request_hex_asbytes.decode("hex")
    udp_request_bytes = array.array('B', res_hex_data)
    
    #result  = custom_udp_parse_announce_request(udp_request_bytes)
    
    
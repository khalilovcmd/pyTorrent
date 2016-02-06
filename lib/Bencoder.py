from Base import Base
from collections import OrderedDict
from os import path

class Bencoder(Base):

    class Bencodes(object):
        INTEGER = 1
        STRING = 2
        LIST = 3
        DICTIONARY = 4

    def __init__(self):
        super(Bencoder, self).__init__()

    def encode(self, data):

        """

        :param dictionary:
        """

        return self.__write_next(data)

    def __write_next(self, data):

        if type(data) is int or type(data) is long:
            return self.__write_int(data)
        elif type(data) is str:
            return self.__write_string(data)
        elif type(data) is OrderedDict:
            return self.__write_dictionary(data)
        elif type(data) is list:
            return self.__write_list(data)

    def __write_int(self,data):

        assert type(data) is int or type(data) is long
        return 'i' + str(data) + 'e'

    def __write_string(self,data):

        assert type(data) is str

        return str(len(data)) + ':' + data

    def __write_dictionary(self,data):

        assert type(data) is OrderedDict

        result = ""
        result += 'd'

        for key,value in data.iteritems():
            result += self.__write_next(key)
            result += self.__write_next(value)

        result += 'e'

        return result

    def __write_list(self,data):

        assert type(data) is list

        result = ""
        result += "l"

        for l in data:
            result += self.__write_next(l)

        result += "e"

        return result

    def decode(self, file):

        """

        :param file:
        :return: :raise ValueError:
        """

        result = None
        torrent = open(file, 'rb')

        while True:

            # to read next 1 byte of the .torrent file
            c = torrent.read(1)

            if not c:
                return result
            else:
                result = self.__read_next(c, torrent)
                self.logger.info(result)

        torrent.close()

        return result

    def __read_integer(self, torrent):

        """
        parsing bencode integer
        :param torrent:
        :return:
        """

        result = ""

        while True:
            c = torrent.read(1)

            if c == 'e':
                return int(result)
            elif c.isdigit():
                result += c
            else:
                return int(result)

    def __read_string(self, torrent):

        # initializing string value length
        """

        :param character:
        :param torrent:
        :return:
        """

        # seek one byte before the current,
        # to read the length of the string from it's original starting point
        torrent.seek(-1, 1)

        c = torrent.read(1)

        length = c
        next = c

        # stop when we encounter character ':'
        while next != ':':

            # continue reading character-by-character
            next = torrent.read(1)
            if next != ':':
                length += next

        return torrent.read(int(length))

    def __read_list(self, torrent):
        """

        :param torrent:
        :return:
        """
        root = []

        while True:

            c = torrent.read(1)

            if c == 'e':
                return root
            else:
                result = self.__read_next(c, torrent)
                root.append(result)

    def __read_dictionary(self, torrent):
        """

        :param torrent:
        :return:
        """
        root = OrderedDict()

        # to keep track of the dictionary key/value pair parsing
        pair_counter = 1

        # to save previously parsed dictionary's "key" or "value"
        key = None
        value = None

        while True:

            # to read next 1 byte of the .torrent file
            c = torrent.read(1)

            if not c:
                return root

            elif pair_counter % 2 == 1 and c == 'e':
                return root

            elif pair_counter % 2 == 1 and c.isdigit():

                # increment pair counter
                pair_counter += 1

                # read dictionary key, assign dictionary entry "key" to parsed result
                key = self.__read_string(torrent)

            elif pair_counter % 2 == 0:

                # increment pair counter
                pair_counter += 1

                # read dictionary value, assign dictionary entry parsed "value"
                value = self.__read_next(c, torrent)

            # assign dictionary entry with "key" and "value"
            if pair_counter % 2 == 1:
                root[key] = value

    def __read_next(self, c, torrent):

        """

        :param c:
        :param torrent:
        :return:
        """
        result = None

        if c.isdigit():
            result = self.__read_string(torrent)

        elif c == 'd':
            result = self.__read_dictionary(torrent)

        elif c == 'l':
            result = self.__read_list(torrent)

        elif c == 'i':
            result = self.__read_integer(torrent)

        return result


def main():
    print('beginning of the end...')

    print Bencoder().encode( {"lists" : [1,2,3,4 ] })
    print Bencoder().decode(r'..\content\torrents\[kat.cr]jobs.2013.1080p.bluray.x264.ac3.etrg.torrent')

    decoded = Bencoder().decode(r'..\content\torrents\[kat.cr]jobs.2013.1080p.bluray.x264.ac3.etrg.torrent')


    f = open('output.torrent', 'wb+')
    f.write(Bencoder().encode(decoded))



if __name__ == "__main__":
    main()

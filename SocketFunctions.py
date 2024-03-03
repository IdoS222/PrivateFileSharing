class SocketFunctions:
    @staticmethod
    def read_from_socket(sock):
        """
        Reading all the data from a socket by getting the length of the data and then reading all the data.
        :param sock: The socket to listen from.
        :return: The data.
        """
        buffer = ""
        lenOfData = ""
        while buffer != ".":
            buffer = sock.recv(1).decode()
            lenOfData += buffer
        return sock.recv(int(lenOfData[:-1])).decode()

    @staticmethod
    def send_data(sock, data):
        """
        Sending all the data with a buffer that is the length of the data.
        :param sock: 
        :param data:
        :return:
        """
        messageToClient = "{}.{}".format(len(data), data).encode()
        sock.send(messageToClient)

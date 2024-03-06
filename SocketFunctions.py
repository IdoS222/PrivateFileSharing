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

        data_length = int(lenOfData[:-1])
        received_data = ""
        while len(received_data) < data_length:
            received_data += sock.recv(data_length - len(received_data)).decode()

        return received_data

    @staticmethod
    def send_data(sock, data):
        """
        Sending all the data with a buffer that is the length of the data.
        :param sock: The socket to send data to.
        :param data: The data to be sent.
        :return: None
        """
        message_to_client = "{}.{}".format(len(data), data).encode()
        sock.send(message_to_client)

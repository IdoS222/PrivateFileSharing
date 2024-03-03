import socket
import json


class TrackerRequest:
    @staticmethod
    def get_files_from_tracker(tracker, user):
        """
        Getting all the files from a tracker that the rank can get.
        :param tracker: The tracker address [ip, port].
        :param user: The user that is sending the request.
        :return: The files.
        """

        filesRequest = json.dumps({
            "requestType": 0,
            "userID": user["userID"],
            "firstName": user["firstName"],
            "lastName": user["lastName"],
            "email": user["email"],
            "rank": user["rank"]
        })

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(tuple(tracker))
        sock.send(filesRequest.encode())

        data = TrackerRequest.read_from_socket(sock)  # TODO: read until empty
        print(data)
        files = json.loads(data)
        return files

    @staticmethod
    def upload_file_to_tracker(tracker, user, fileName, fileSize, pieceSize, amountOfPieces, fileVisibility, fileOwners,
                               fileUploader):
        """
        Sending a new file to the tracker.
        :param tracker: The tracker address [ip, port].
        :param user: The user that is sending the request.
        :param fileName: The name of the file.
        :param fileSize: The size of the file.
        :param pieceSize: The size of one piece.
        :param amountOfPieces: The amount of pieces that make the file.
        :param fileVisibility: The visibility of the file.
        :param fileOwners: The owners of the file. (a list of address that has the complete file)
        :param fileUploader: The uploader of the file.
        :return: A json dump of the status of the request
        """

        newFileRequest = json.dumps({
            "requestType": 1,
            "userID": user["userID"],
            "firstName": user["firstName"],
            "lastName": user["lastName"],
            "email": user["email"],
            "rank": user["rank"],
            "fileName": fileName,
            "fileSize": fileSize,
            "pieceSize": pieceSize,
            "amountOfPieces": amountOfPieces,
            "fileVisibility": fileVisibility,
            "fileOwners": fileOwners,
            "fileUploader": fileUploader
        })

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(tuple(tracker))
        sock.send(newFileRequest.encode())

        data = sock.recv(1024).decode()
        status = json.loads(data)
        return status

    @staticmethod
    def start_download(tracker, user, fileID, fileName):
        """
        Getting the list of peers from the tracker.
        :param tracker: The tracker address [ip, port].
        :param user: The user that is sending the request.
        :param fileID: The id of the file in the database.
        :param fileName: The name of the file.
        :return: The list of the peers that have the file.
        """

        startDownloadRequest = json.dumps({
            "requestType": 2,
            "userID": user["userID"],
            "firstName": user["firstName"],
            "lastName": user["lastName"],
            "email": user["email"],
            "rank": user["rank"],
            "fileID": fileID,
            "fileName": fileName
        })

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(tuple(tracker))
        sock.send(startDownloadRequest.encode())

        data = TrackerRequest.read_from_socket(sock)  # TODO: read until empty
        listOfPeers = json.loads(data)
        return listOfPeers

    @staticmethod
    def finish_download(tracker, user, fileID, fileName):
        """
        Telling the tracker we have the full file and to add us to the list of owners for this file
        :param tracker: The tracker address [ip, port].
        :param user: The user that is sending the request.
        :param fileID: The id of the file in the database.
        :param fileName: The name of the file.
        :return: A json dump of the status of the request
        """

        finishDownloadRequest = json.dumps({
            "requestType": 3,
            "userID": user["userID"],
            "firstName": user["firstName"],
            "lastName": user["lastName"],
            "email": user["email"],
            "rank": user["rank"],
            "fileID": fileID,
            "fileName": fileName
        })

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(tuple(tracker))
        sock.send(finishDownloadRequest.encode())

        data = sock.recv(1024).decode()
        status = json.loads(data)
        return status

    @staticmethod
    def delete_file(tracker, user, fileID, fileName):
        """
        Telling the tracker to delete a file.
        :param tracker: The tracker address [ip, port].
        :param user: The user that is sending the request.
        :param fileID: The id of the file in the database.
        :param fileName: The name of the file.
        :return: A json dump of the status of the request
        """

        finishDownloadRequest = json.dumps({
            "requestType": 4,
            "userID": user["userID"],
            "firstName": user["firstName"],
            "lastName": user["lastName"],
            "email": user["email"],
            "rank": user["rank"],
            "fileID": fileID,
            "fileName": fileName
        })

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(tuple(tracker))
        sock.send(finishDownloadRequest.encode())

        data = sock.recv(1024).decode()
        status = json.loads(data)
        return status

    @staticmethod
    def get_tracker_data(tracker, user):
        """
        Get the tracker data.
        :param tracker: The tracker address [ip, port].
        :param user: The user that is sending the request.
        :return: The files.
        """

        dataRequest = json.dumps({
            "requestType": 6,
            "userID": user["userID"],
            "firstName": user["firstName"],
            "lastName": user["lastName"],
            "email": user["email"],
            "rank": user["rank"]
        })

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(tuple(tracker))
        sock.send(dataRequest.encode())

        data = sock.recv(1024).decode()
        trackerData = json.loads(data)
        return trackerData

    @staticmethod
    def read_from_socket(socket):
        """
        Reading from a socket until empty.
        :param socket: Socket.
        :return: The data from the socket.
        """
        data = socket.recv(1024)
        while data != b'':
            print(data)
            data += socket.recv(1024)
        return data

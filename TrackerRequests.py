import socket
import json
from SocketFunctions import SocketFunctions


class TrackerRequest:
    @staticmethod
    def get_files_from_tracker(tracker, user):
        """
        Getting all the files from a tracker that the rank can get.
        :param tracker: The tracker address [ip, port].
        :param user: The user that is sending the request.
        :return: The files.
        """
        try:
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
            SocketFunctions.send_data(sock, filesRequest)

            data = SocketFunctions.read_from_socket(sock)
            files = json.loads(data)
            return files
        except Exception:
            return {"errorMessage": "Couldn't get the files from the tracker"}

    @staticmethod
    def upload_file_to_tracker(tracker, user, fileName, fileSize, pieceSize, amountOfPieces, fileVisibility, fileOwners,
                               fileUploader, listOfHashes):
        """
        Sending a new file to the tracker.
        :param tracker: The tracker address [ip, port].
        :param user: The user that is sending the request.
        :param fileName: The name of the file.
        :param fileSize: The size of the file.
        :param pieceSize: The size of one piece.
        :param amountOfPieces: The number of pieces that make the file.
        :param fileVisibility: The visibility of the file.
        :param fileOwners: The owners of the file. (a list of address that has the complete file)
        :param fileUploader: The uploader of the file.
        :param listOfHashes: A list of hashes of all the pieces.
        :return: A json dump of the status of the request
        """
        try:
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
                "fileUploader": fileUploader,
                "listOfHashes": listOfHashes
            })

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(tuple(tracker))
            SocketFunctions.send_data(sock, newFileRequest)

            data = SocketFunctions.read_from_socket(sock)
            status = json.loads(data)
            return status
        except Exception:
            return {"errorMessage": "Couldn't upload the file to the server"}

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
        try:
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
            SocketFunctions.send_data(sock, startDownloadRequest)

            data = SocketFunctions.read_from_socket(sock)
            answer = json.loads(data)
            return answer
        except Exception as e:
            print(e)
            return {"errorMessage": "Couldn't start the download"}

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
        try:
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
            SocketFunctions.send_data(sock, finishDownloadRequest)

            data = SocketFunctions.read_from_socket(sock)
            status = json.loads(data)
            return status
        except Exception:
            return {"errorMessage": "Couldn't send the finish download notification to the tracker"}

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
        try:
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
            SocketFunctions.send_data(sock, finishDownloadRequest)

            data = SocketFunctions.read_from_socket(sock)
            status = json.loads(data)
            return status
        except Exception:
            return {"errorMessage": "Couldn't delete the file from the tracker"}

    @staticmethod
    def get_tracker_data(tracker, user):
        """
        Get the tracker data.
        :param tracker: The tracker address [ip, port].
        :param user: The user that is sending the request.
        :return: The files.
        """
        try:
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
            SocketFunctions.send_data(sock, dataRequest)

            data = SocketFunctions.read_from_socket(sock)
            trackerData = json.loads(data)
            return trackerData
        except Exception:
            return {"errorMessage": "Couldn't get the tracker data"}

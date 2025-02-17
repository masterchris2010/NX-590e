import socket
import threading
import time
import logging

class TCPClient:
    def __init__(self, parent_object):
        self.ReceiveIsRunning = False
        self.characterSet = 'ISO-8859-1'
        self.dataInputStream = None
        self.dataOutputStream = None
        self.mySocket = None
        self.objectID = 0
        self.parentObject = parent_object
        self.serverIP = "192.168.0.50"
        self.serverPort = 3434

    def Init(self, ServerIP, ServerPort, ObjectID):
        self.serverIP = ServerIP
        self.serverPort = ServerPort
        self.objectID = ObjectID
        self.InitSocket()

    def Open(self, Timeout):
        if self.mySocket is None:
            self.InitSocket()
        try:
            self.mySocket.settimeout(Timeout)
            self.mySocket.connect((self.serverIP, self.serverPort))
            self.dataOutputStream = self.mySocket.makefile('wb')
            self.dataInputStream = self.mySocket.makefile('rb')
            self.Receive_Start()
            return True
        except socket.timeout:
            self.CloseAndDestroy()
            return False
        except Exception as e:
            logging.error("TCP: Error", exc_info=e)
            return False

    def Close(self):
        if self.mySocket is None or not self.is_socket_connected() or not self.ReceiveIsRunning:
            return False
        try:
            self.ReceiveIsRunning = False
            return True
        except Exception as e:
            logging.error("TCP: Error", exc_info=e)
            return False

    def Send(self, sBuffer):
        try:
            return self.SendBytes(sBuffer.encode(self.characterSet))
        except UnicodeEncodeError as e:
            logging.error("Encoding Error", exc_info=e)
            return False

    def SendBytes(self, bBuffer):
        if self.mySocket is None or not self.is_socket_connected():
            return False
        try:
            self.dataOutputStream.write(bBuffer)
            self.dataOutputStream.flush()
            return True
        except Exception as e:
            logging.error("TCP: Error", exc_info=e)
            return False

    def InitSocket(self):
        try:
            self.mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except Exception as e:
            logging.error("TCP: Error", exc_info=e)

    def CloseAndDestroy(self):
        if self.mySocket:
            try:
                self.mySocket.close()
                self.mySocket = None
            except Exception as e:
                logging.error("TCP: Error", exc_info=e)

    def Receive_Start(self):
        tReceive_Engine = threading.Thread(target=self.Receive_Engine)
        tReceive_Engine.start()

    def Receive_Engine(self):
        self.ReceiveIsRunning = True
        while self.mySocket and self.is_socket_connected() and self.ReceiveIsRunning:
            try:
                dataCount = self.mySocket.recv(4096)
                if dataCount:
                    msg = dataCount.decode(self.characterSet)
                    self.parentObject.TCPClients_OnNewBuffer(self.objectID, msg)
                time.sleep(0.02)
            except TimeoutError:
                continue
            except Exception as e:
                logging.error("TCP: Error", exc_info=e)
        self.CloseAndDestroy()

    def indexOf(self, data, pattern, dataLength):
        failure = self.computeFailure(pattern)
        j = 0
        i = 0
        while i < dataLength:
            while j > 0 and pattern[j] != data[i]:
                j = failure[j - 1]
            if pattern[j] == data[i]:
                j += 1
            if j == len(pattern):
                return (i - len(pattern)) + 1
            i += 1
        return -1

    def computeFailure(self, pattern):
        failure = [0] * len(pattern)
        j = 0
        i = 1
        while i < len(pattern):
            while j > 0 and pattern[j] != pattern[i]:
                j = failure[j - 1]
            if pattern[j] == pattern[i]:
                j += 1
            failure[i] = j
            i += 1
        return failure

    def is_socket_connected(self):
        try:
            self.mySocket.send(b'')
        except socket.error:
            return False
        return True
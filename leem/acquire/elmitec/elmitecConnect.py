# -*- coding: utf-8 -*-
"""
MIT License

Copyright (c) 2019 Dr. Helder Marchetto

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import socket
import time
import numpy as np
import struct
import sys


def is_number(s):
    """This is used to check if the input string can be used as a number"""
    try:
        float(s)
        return True
    except ValueError:
        return False


def getTcp(s, TCPString, isFlt=True, isInt=False, asIs=False):
    s.send(TCPString.encode("utf-8"))
    retStr = TCPBlockingReceive(s)
    if asIs:
        # print('is asIs = ', TCPString, retStr)
        return retStr
    elif isInt:
        if is_number(retStr):
            return int(retStr)
        else:
            return 0
    elif isFlt:
        if is_number(retStr):
            return float(retStr)
        else:
            return 0.0
    else:
        return retStr


def setTcp(s, TCPString, Value):
    TCPString = TCPString.strip() + " " + Value.strip()
    s.send(TCPString)
    return TCPBlockingReceive(s)


def TCPBlockingReceive(s):
    Bytereceived = "0"
    szData = ""
    while ord(Bytereceived) != 0:
        ReceivedLength = 0
        while ReceivedLength == 0:
            Bytereceived = s.recv(1)
            # print('Bytereceived=',Bytereceived,'ord(Bytereceived)=',ord(Bytereceived))
            ReceivedLength = len(Bytereceived)
        if ord(Bytereceived) != 0:
            szData = szData + Bytereceived.decode("utf-8")
    return szData


class elmitecConnect:
    Leem2000Connected = False
    UviewConnected = False

    def __enter__(self):
        return self

    def __init__(
        self, ip="192.168.178.26", LEEMport=5566, UVIEWport=5570, directConnect=True
    ):
        if not isinstance(ip, str):
            print("LEEM_Host must be a string. Using localhost instead.")
            self.ip = socket.gethostbyname(socket.gethostname())
        else:
            self.ip = ip
        if not isinstance(LEEMport, int):
            print("LEEMport must be an integer. Using 5566.")
            self.LEEMport = 5566
        else:
            self.LEEMport = LEEMport

        if not isinstance(UVIEWport, int):
            print("UVIEWport must be an integer. Using 5570.")
            self.UVIEWport = 5570
        else:
            self.UVIEWport = UVIEWport

        self.lastTime = time.time()
        if directConnect:
            print(
                "Connect with ip="
                + str(self.ip)
                + ", LEEMport="
                + str(self.LEEMport)
                + ", UVIEWport="
                + str(self.UVIEWport)
            )
            self.oLeem = oLeem(ip=self.ip, port=self.LEEMport)
            self.oUview = oUview(ip=self.ip, port=self.UVIEWport)

    def __exit__(self, type, value, traceback):
        # print("Destroying", self)
        try:
            self.oLeem.disconnect
        except AttributeError:
            print("oLEEM not open yet")
        try:
            self.oUview.disconnect
        except AttributeError:
            print("oUview not open yet")

    def __repr__(self):
        try:
            if self.oLeem.Leem2000Connected:
                leemStr = str(
                    "LEEM2000 connected (ip=%s,port=%4i)" % (self.ip, self.LEEMport)
                )
            else:
                leemStr = str("LEEM2000 not connected")
            if self.oUview.UviewConnected:
                uviewStr = str(
                    "uView connected (ip=%s,port=%4i)" % (self.ip, self.UVIEWport)
                )
            else:
                uviewStr = str("uView not connected")
            return "\n".join([leemStr, uviewStr])
        except AttributeError:
            return "Object not defined"


class oLeem:
    Leem2000Connected = False

    def __enter__(self):
        return self

    def __init__(self, ip="192.168.178.26", port=5566, directConnect=True):
        if not isinstance(ip, str):
            print("LEEM_Host must be a string. Using localhost instead.")
            self.ip = socket.gethostbyname(socket.gethostname())
        else:
            self.ip = ip

        if not isinstance(port, int):
            print("LEEM_Port must be an integer. Using 5566.")
            self.port = 5566
        else:
            self.port = port

        self.lastTime = time.time()

        if directConnect:
            print("Connect with ip=" + str(self.ip) + ", port=" + str(self.port))
            self.connect()

    def __exit__(self, type, value, traceback):
        # print("Destroying", self)
        if self.Leem2000Connected:
            # print('Exit without closing connections... close connections')
            self.s.send("clo".encode("utf-8"))
            self.s.close()
            self.Leem2000Connected = False
        if self.Leem2000Connected:
            # print('Exit without closing connections... close connections')
            self.s.send("clo".encode("utf-8"))
            self.s.close()
            self.Leem2000Connected = False

    def connect(self):
        if self.Leem2000Connected:
            print('Already connected ... exit "connect" method')
            return
        else:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print("connecting leem with")
            print(self.ip)
            print(self.port)
            self.s.connect((self.ip, self.port))
            self.Leem2000Connected = True
            # Start string communication
            getTcp(self.s, "asc", False, False, True)
            # Get list of devices
            self.updateModules()
            self.updateValues()
            print("Connected. %i modules found " % len(self.Mnemonic))
            print("#########################################")
            print("To see which devices are available, type:")
            print("for i in oLeem.Modules.values(): print(i)")
            print("for i in oLeem.Mnemonic.values(): print(i)")
            print("#########################################")
            print("To check the value of a device, type:")
            print("print(oLeem.getValue('FL')")

    def testConnect(self):
        if self.Leem2000Connected:
            print('Already connected ... exit "connect" method')
            return True
        else:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.settimeout(5)  # 5 seconds timeout
            t = time.time()
            try:
                self.s.connect((self.ip, self.port))
                print("connected in " + str(time.time() - t) + " sec")
                self.s.settimeout(None)
                self.s.close()
                return True
            except:
                print("connection not possible")
                print("please check: that LEEM is running")
                print("              the IP address is correct")
                print("              the PORT is the same activated in LEEM2000")
                return False
            else:
                return False

    def setIP(self, IP):
        if self.Leem2000Connected:
            print("Already connected ... close connection first")
            return
        else:
            if type(IP) != str:
                print("The IP has to be a string. Please use this synthax:")
                print("object.setIP('192.168.1.0')")
                print("or")
                print("object.setIP('localhost')")
                return
            self.ip = str(IP)

    def setPort(self, port):
        if self.Leem2000Connected:
            print("Already connected ... close connection first")
            return
        else:
            if type(port) != int:
                print("The port has to be a number. Please use this synthax:")
                print("object.setPort(5566)")
                return
            self.port = str(port)

    def disconnect(self):
        if self.Leem2000Connected:
            self.s.send("clo".encode("utf-8"))
            self.s.close()
            self.Leem2000Connected = False
            print("Disconnected!")

    def updateValues(self):
        if not self.Leem2000Connected:
            print("Please connect first")
            return None
        else:
            self.Values = {}
            for x in self.Mnemonic:
                data = getTcp(self.s, "get " + self.Modules[x], True, False, False)
                if is_number(data):
                    self.Values[x] = float(data)

    def updateModules(self):
        if not self.Leem2000Connected:
            print("Please connect first")
            return None
        else:
            # Get list of devices
            self.nModules = getTcp(self.s, "nrm", False, True, False)
            # Get list of devices
            self.Modules = {}
            self.Mnemonic = {}
            self.invModules = {}
            self.invMnemonic = {}
            self.lowLimit = {}
            self.highLimit = {}
            self.MnemonicUp = {}
            self.ModulesUp = {}
            for x in range(self.nModules):
                data = getTcp(self.s, "nam " + str(x), False, False, True)
                if not data in ["", "no name", "invalid", "disabled"]:
                    self.Modules[x] = data
                    self.ModulesUp[x] = data.upper()
                    self.invModules[data.upper()] = x
                data = getTcp(self.s, "mne " + str(x), False, False, True)
                if not data in ["", "no name", "invalid", "disabled"]:
                    self.Mnemonic[x] = data
                    self.MnemonicUp[x] = data.upper()
                    self.invMnemonic[data.upper()] = x
                ll = self.getLowLimit(x, isNotSetup=False)
                hl = self.getHighLimit(x, isNotSetup=False)
                if (not ll in ["", "no name", "invalid", "disabled"]) and is_number(ll):
                    self.lowLimit[x] = ll
                if (not hl in ["", "no name", "invalid", "disabled"]) and is_number(hl):
                    self.highLimit[x] = hl

    def get(self, TCPString, module):
        # check if the input is a number or a string
        if TCPString[-1] != " ":
            TCPString += " "
        if is_number(module):
            m = int(module)
            if m in self.Mnemonic:
                data = getTcp(self.s, TCPString + str(m), False, False, True)
                if not data in ["", "invalid"] and is_number(data):
                    return float(data)
                else:
                    return (
                        "invalid number " + str(m) + ". Return from leem=" + str(data)
                    )
            else:
                return "Module number " + str(module) + " not found"
        else:
            module = str(module)
            if module.upper() in self.invModules:
                data = getTcp(
                    self.s,
                    TCPString + (self.invModules[module.upper()]),
                    False,
                    False,
                    True,
                )
                if (not data in ["", "invalid"]) and is_number(data):
                    return float(data)
                else:
                    return "invalid"
            elif module.upper() in self.invMnemonic:
                data = getTcp(
                    self.s,
                    TCPString + str(self.invMnemonic[module.upper()]),
                    False,
                    False,
                    True,
                )
                if not data in ["", "invalid"] and is_number(data):
                    return float(data)
                else:
                    return "invalid"
            else:
                return "Module " + module + " not found"

    def getValue(self, module):
        if not self.Leem2000Connected:
            print("Please connect first")
            return None
        else:
            # check if the input is a number or a string
            if (time.time() - self.lastTime) < 0.3:
                time.sleep(0.3)
            return self.get("get ", module)

    def setValue(self, module, value):
        if not self.Leem2000Connected:
            print("Please connect first")
            return None
        else:
            # check if the input value is a number or a string
            if not is_number(value):
                return "Value must be a number"
            else:
                value = str(value)
            # check if the input module is a number or a string
            self.lastTime = time.time()
            if is_number(module):
                m = int(module)
                return (
                    getTcp(self.s, "set " + str(m) + "=" + value, False, False, True)
                    == "0"
                )
            else:
                if (module.upper() in self.MnemonicUp.values()) or (
                    module.upper() in self.ModulesUp.values()
                ):
                    return (
                        getTcp(
                            self.s,
                            "set " + str(module) + "=" + value,
                            False,
                            False,
                            True,
                        )
                        == "0"
                    )
                else:
                    return False

    def getLowLimit(self, module, isNotSetup=True):
        if not self.Leem2000Connected:
            print("Please connect first")
            return None
        else:

            if (time.time() - self.lastTime) < 0.3 and isNotSetup:
                time.sleep(0.3)
            self.lastTime = time.time()
            TCPString = "psl "
            return self.get(TCPString, module)

    def getHighLimit(self, module, isNotSetup=True):
        if not self.Leem2000Connected:
            print("Please connect first")
            return None
        else:
            if (time.time() - self.lastTime) < 0.3 and isNotSetup:
                time.sleep(0.3)
            self.lastTime = time.time()
            TCPString = "psh "
            return self.get(TCPString, module)

    def getFoV(self):
        if not self.Leem2000Connected:
            print("Please connect first")
            return None
        else:
            # check if the input is a number or a string
            data = getTcp(self.s, "prl", False, False, True)
            strSplit = data.partition(":")
            if strSplit[1] == ":":
                part = data.partition("\xb5")
                if part[1] == "\xb5":
                    FoVStr = part[0]
                    if is_number(FoVStr):
                        return (
                            float(FoVStr),
                            True,
                        )  # True means that the FoV is a number
            return (data, False)  # False means that no useful number is given out

    def getModifiedModules(self):
        if not self.Leem2000Connected:
            print("Please connect first")
            return None
        else:
            # check if the input is a number or a string
            data = getTcp(self.s, "chm", False, False, True)
            if data != "0":
                arr = data.split()
                nChanges = int(arr[0])
                del arr[0]
                Changes = []
                for i in range(nChanges):
                    Changes.append(
                        {
                            "moduleName": self.Modules[int(arr[i * 2])],
                            "moduleNr": int(arr[i * 2]),
                            "NewValue": float(arr[1 + i * 2]),
                        }
                    )
                return (nChanges, Changes)
            else:
                return (0, 0)


class oUview(object):
    UviewConnected = False

    def __enter__(self):
        return self

    def __init__(self, ip="172.23.106.79", port=5570, directConnect=True):
        if not isinstance(ip, str):
            print("Uview_Host must be a string. Using localhost instead.")
            self.ip = socket.gethostbyname(socket.gethostname())
        else:
            self.ip = ip

        if not isinstance(port, int):
            print("Uview_Port must be an integer. Using 5570.")
            self.port = 5570
        else:
            self.port = port

        self.lastTime = time.time()

        if directConnect:
            print("Connect with ip=" + str(self.ip) + ", port=" + str(self.port))
            self.connect()

    def __exit__(self, type, value, traceback):
        # print("Destroying", self)
        if self.UviewConnected:
            # print('Exit without closing connections... close connections')
            self.s.send("clo".encode("utf-8"))
            self.s.close()
            self.UviewConnected = False

    def connect(self):
        if self.UviewConnected:
            print('Already connected ... exit "connect" method')
            return None
        else:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((self.ip, self.port))
            self.UviewConnected = True
            # Start string communication
            TCPString = "asc"
            self.s.send(TCPString.encode("utf-8"))
            data = TCPBlockingReceive(self.s)

    def testConnect(self):
        if self.UviewConnected:
            print('Already connected ... exit "connect" method')
            return True
        else:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.settimeout(5)  # 5 seconds timeout
            t = time.time()
            try:
                self.s.connect((self.ip, self.port))
                print("connected in " + str(time.time() - t) + " sec")
                self.s.settimeout(None)
                self.s.close()
                return True
            except:
                print("connection not possible")
                print("please check: that Uview is running")
                print("              the IP address is correct")
                print("              the PORT is the same activated in Uview")
                return False
            else:
                return False

    def setIP(self, IP):
        if self.UviewConnected:
            print('Already connected ... exit "connect" method')
            return
        else:
            if type(IP) != str:
                print("The IP has to be a string. Please use this synthax:")
                print("object.setIP('192.168.1.0')")
                print("or")
                print("object.setIP('localhost')")
                return
            self.ip = str(IP)

    def setPort(self, port):
        if self.UviewConnected:
            print('Already connected ... exit "connect" method')
            return
        else:
            if type(port) != int:
                print("The port has to be a number. Please use this synthax:")
                print("object.setPort(5570)")
                return
            self.port = str(port)

    def disconnect(self):
        if self.UviewConnected:
            self.s.send("clo".encode("utf-8"))
            self.s.close()
            self.UviewConnected = False
            print("Disconnected!")

    def getImage(self):
        if not self.UviewConnected:
            print("Please connect first")
            return None
        else:
            TCPString = "ida 0 0"
            self.s.send(TCPString.encode("utf-8"))
            header = "".encode("utf-8")
            for i in range(19):
                header += self.s.recv(1)
            print(header)
            arr = header.split()
            if len(arr) != 3:
                print("Wrong header. Exit")
                return
            xs = int(arr[1])
            ys = int(arr[2])
            img = np.zeros((xs, ys), dtype=np.uint16)  # must be 16 bit
            if sys.version_info >= (2, 7):
                for i in range(ys):
                    img[:, i] = struct.unpack("{}H".format(xs), self.s.recv(xs * 2))
            else:
                for i in range(ys):
                    img[:, i] = struct.unpack("{0}H".format(xs), self.s.recv(xs * 2))
            void = self.s.recv(1)
            return img

    def exportImage(self, fileName, imgFormat="0", imgContents="0"):
        if not self.UviewConnected:
            print("Please connect first")
            return None
        else:
            TCPString = (
                "exp " + str(imgFormat) + ", " + str(imgContents) + ", " + str(fileName)
            )
            self.s.send(TCPString.encode("utf-8"))
            data = TCPBlockingReceive(self.s)
            return len(data) == 0

    def setAvr(self, avr="0"):
        if not self.UviewConnected:
            print("Please connect first")
            return None
        else:
            if not is_number(avr):
                return
            numAvr = int(avr)
            if (numAvr >= 0) and (numAvr <= 99):
                retVal = setTcp(self.s, "avr", str(numAvr))
                return retVal

    def getAvr(self):
        if not self.UviewConnected:
            print("Please connect first")
            return None
        else:
            TCPString = "avr"
            self.s.send(TCPString.encode("utf-8"))
            data = TCPBlockingReceive(self.s)
            if is_number(data):
                return int(data)
            else:
                return 0

    def acquireSingleImg(self, id=-1):
        if not self.UviewConnected:
            print("Please connect first")
            return None
        else:
            TCPString = "asi " + str(id)
            self.s.send(TCPString.encode("utf-8"))
            return TCPBlockingReceive(self.s)

    def setAcqState(self, acqState=-1):
        if not self.UviewConnected:
            print("Please connect first")
            return None
        else:
            if (acqState == -1) or (acqState == "-1"):
                acqState = self.aip()
            acqState = str(acqState)
            if (acqState != "0") or (acqState != "1"):
                return
            TCPString = "aip " + str(acqState)
            self.s.send(TCPString.encode("utf-8"))
            return TCPBlockingReceive(self.s)

    def getAcqState(self):
        return self.aip()

    def aip(self):
        if not self.UviewConnected:
            print("Please connect first")
            return None
        else:
            TCPString = "aip"
            self.s.send(TCPString.encode("utf-8"))
            return TCPBlockingReceive(self.s) == "1"

    def getROI(self):
        if not self.UviewConnected:
            print("Please connect first")
            return None
        else:
            xmi = getTcp(self.s, "xmi", False, True)
            xma = getTcp(self.s, "xma", False, True)
            ymi = getTcp(self.s, "ymi", False, True)
            yma = getTcp(self.s, "yma", False, True)
            return [xmi, ymi, xma, yma]

    def getCameraSize(self):
        if not self.UviewConnected:
            print("Please connect first")
            return None
        else:
            gcs = getTcp(self.s, "gcs", False, False, True)
            spl = gcs.split()
            if len(spl) == 2:
                if is_number(spl[0]) and is_number(spl[1]):
                    return [int(spl[0]), int(spl[1])]
                else:
                    print("Uview image size format error")
                    return [-1, -1]
            else:
                print("Uview image size format error")
                return [-1, -1]

    def getExposureTime(self):
        if not self.UviewConnected:
            print("Please connect first")
            return None
        else:
            ext = getTcp(self.s, "ext", True, False, False)
            return ext

    def setExposureTime(self, ext):
        if not self.UviewConnected:
            print("Please connect first")
            return None
        else:
            setTcp(self.s, "ext", ext)
            return

    def getNrActiveMarkers(self):
        if not self.UviewConnected:
            print("Please connect first")
            return None
        else:
            print("call nMarkersStr")
            nMarkersStr = getTcp(self.s, "mar -1", False, False, True)
            print("nMarkersStr returns = ", nMarkersStr)
            nMarkers = nMarkersStr.split()
            if len(nMarkers) <= 1:
                return 0
            if not is_number(nMarkers[0]):
                return 0
            nm = int(nMarkers[0])
            del nMarkers[0]
            markers = []
            for i in nMarkers:
                markers.append(int(i))
            return [nm, markers]

    def getMarkerInfo(self, marker):
        if not self.UviewConnected:
            print("Please connect first")
            return None
        else:
            if not is_number(marker):
                print("Marker value must be a valid number")
                return
            markerInfo = setTcp(self.s, "mar", str(marker))
            splitMarker = markerInfo.split()
            if len(splitMarker) != 7:
                return 0
            typeNr = int(splitMarker[2])
            if typeNr == 0:
                myType = "line"
            elif typeNr == 1:
                myType = "horizline"
            elif typeNr == 2:
                myType = "vertline"
            elif typeNr == 5:
                myType = "circle"
            elif typeNr == 9:
                myType = "text"
            elif typeNr == 10:
                myType = "cross"
            else:
                myType = "unknown"
            return {
                "marker": marker,
                "imgNr": int(splitMarker[1]),
                "type": myType,
                "typeNr": typeNr,
                "pos": [
                    int(splitMarker[3]),
                    int(splitMarker[4]),
                    int(splitMarker[5]),
                    int(splitMarker[6]),
                ],
            }


"""
import elmitecConnect as ec
oec = 0
oec = ec.elmitecConnect()
img = oec.oUview.getImage()

import matplotlib
import matplotlib.pyplot as plt
plt.imshow(img, cmap=plt.cm.gray)
"""

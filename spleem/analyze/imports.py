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

"""
Editor: Cameron Johnson
"""

"""
I had to comment out the self.lp = self.leemParameters() in the getImage() method 
because it would print an endless list of "addtional gauges"
"""


import struct, os
import numpy as np
import bisect as bs
import time as tm

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class ReadUView:
    def __init__(self) -> None:
        """Initializes the ReadUView object"""

    def __repr__(self):
        try:
            return str(
                "Filename = %s\nimgSize = (%i,%i)"
                % (self.fn, self.imageWidth, self.imageHeight)
            )
        except AttributeError:
            return str("Object not defined")

    def getImage(self, fn) -> np.ndarray:
        """Returns the uview images as numpy array"""
        self.fn = fn

        with open(self.fn, mode="rb") as file:  # b is important -> binary
            self.fc = file.read()

        self.fh = self.fileHeader()
        self.ih = self.imageHeader()

        totalHeaderSize = (
            self.headerSize
            + self.imageHeadersize
            + self.attachedMarkupSize
            + self.LEEMDataVersion
        )

        head = self.headerSize
        imhead = self.imageHeadersize + self.attachedMarkupSize + self.LEEMDataVersion
        h = self.imageHeight
        w = self.imageWidth
        imlen = imhead + h * w * 2

        # print('rotateMask:{}, desired_rotation:{}, rotation_offset:{}'.format(self.rotateMask,self.desired_rotation,self.rotation_offset))
        t0 = tm.perf_counter()
        ims = []
        n = self.nrImages
        if n == 3:
            for j in range(n):
                if j < (n - 1):
                    imdat = self.fc[head + j * imlen + imhead : head + (j + 1) * imlen]
                else:
                    imdat = self.fc[len(self.fc) - h * w * 2 : len(self.fc)]
                ims.append(np.reshape(struct.unpack(str(w * h) + "H", imdat), (h, w)))
        else:
            for j in range(n):
                imdat = self.fc[head + j * imlen + imhead : head + (j + 1) * imlen]
                ims.append(np.reshape(struct.unpack(str(w * h) + "H", imdat), (h, w)))
        # print(tm.perf_counter()-t0)
        # ims.append(  np.reshape(  struct.unpack(str(w*h)+'H',self.fc[size-1-(n-j)*w*h*2:size-1-((n-j)-1)*w*h*2]), (h,w)  )  )
        # return self.fc
        return ims

    def get_all_images(self, folder: "Path") -> list[np.ndarray]:
        frames = []
        for file in os.listdir(folder):
            if file.endswith(".dat"):
                frames.append(self.getImage(folder / file))

        return frames

    def fileHeader(self, verbose=False) -> None:
        """Loads the contents of the file header"""
        # must supply the file contents (fc). These are read with the open command in 'rb' mode

        self.UK_id = "".join(map(chr, self.fc[0 : self.fc.index(0)]))
        self.UK_size = int.from_bytes(self.fc[20:22], byteorder="little")
        self.UK_version = int.from_bytes(self.fc[22:24], byteorder="little")
        self.UK_bitsPerPixel = int.from_bytes(self.fc[24:26], byteorder="little")

        if self.UK_version >= 8:
            self.UK_cameraBitsPerPixel = int.from_bytes(
                self.fc[26:28], byteorder="little"
            )
            self.MCPDiameterInPixels = int.from_bytes(
                self.fc[28:30], byteorder="little"
            )
            self.hBinning = int.from_bytes(self.fc[30:31], byteorder="little")
            self.vBinning = int.from_bytes(self.fc[31:32], byteorder="little")
        else:
            voidNr = int(0)
            self.UK_cameraBitsPerPixel = voidNr
            self.MCPDiameterInPixels = voidNr
            self.hBinning = voidNr
            self.vBinning = voidNr

        if self.UK_version >= 2:
            self.imageWidth = int.from_bytes(self.fc[40:42], byteorder="little")
            self.imageHeight = int.from_bytes(self.fc[42:44], byteorder="little")
            self.nrImages = int.from_bytes(self.fc[44:46], byteorder="little")
        else:
            voidNr = int(0)
            self.imageWidth = voidNr
            self.imageHeight = voidNr
            self.nrImages = voidNr

        if self.UK_version >= 7:
            self.attachedRecipeSize = int.from_bytes(self.fc[46:48], byteorder="little")
        else:
            self.attachedRecipeSize = int(0)

        self.hasRecipe = self.attachedRecipeSize > 0
        self.fixedRecipeSize = 128

        if self.hasRecipe:
            self.headerSize = 104 + 128
        else:
            self.headerSize = 104

        if verbose:
            print("headerSize = %i" % self.headerSize)
            print("UK_id = " + self.UK_id)
            print("UK_size = " + str(self.UK_size))
            print("UK_version = " + str(self.UK_version))
            print("UK_bitsPerPixel = " + str(self.UK_bitsPerPixel))
            print("UK_cameraBitsPerPixel = " + str(self.UK_cameraBitsPerPixel))
            print("MCPDiameterInPixels = " + str(self.MCPDiameterInPixels))
            print("hBinning = " + str(self.hBinning))
            print("vBinning = " + str(self.vBinning))
            print("imageWidth = " + str(self.imageWidth))
            print("imageHeight = " + str(self.imageHeight))
            print("nrImages = " + str(self.nrImages))
            print("attachedRecipeSize = " + str(self.attachedRecipeSize))
            print("hasRecipe = " + str(self.hasRecipe))

    def imageHeader(self, verbose=False) -> None:
        """Loads the contents of the image header"""
        fp = self.headerSize  # file pointer
        self.imageHeadersize = int.from_bytes(self.fc[fp : fp + 2], byteorder="little")
        self.version = int.from_bytes(self.fc[fp + 2 : fp + 4], byteorder="little")
        self.colorScaleLow = int.from_bytes(
            self.fc[fp + 4 : fp + 6], byteorder="little"
        )
        self.colorScaleHigh = int.from_bytes(
            self.fc[fp + 6 : fp + 8], byteorder="little"
        )
        self.imageTime = int.from_bytes(self.fc[fp + 8 : fp + 16], byteorder="little")
        self.maskXShift = int.from_bytes(self.fc[fp + 16 : fp + 18], byteorder="little")
        self.maskYShift = int.from_bytes(self.fc[fp + 18 : fp + 20], byteorder="little")
        self.rotateMask = int.from_bytes(
            self.fc[fp + 20 : fp + 22], byteorder="little", signed=False
        )
        self.attachedMarkupSize = int.from_bytes(
            self.fc[fp + 22 : fp + 24], byteorder="little"
        )
        self.hasAttachedMarkup = self.attachedMarkupSize != 0

        if self.hasAttachedMarkup:
            self.attachedMarkupSize = 128 * ((self.attachedMarkupSize // 128) + 1)

        self.spin = int.from_bytes(self.fc[fp + 24 : fp + 26], byteorder="little")
        self.LEEMDataVersion = int.from_bytes(
            self.fc[fp + 26 : fp + 28], byteorder="little"
        )
        fp = fp + 28

        if self.version > 5:
            self.hasLEEMData = True
            self.LEEMDataStartPos = fp
            self.LEEMData = struct.unpack("240c", self.fc[fp : fp + 240])
            fp = fp + 240
            self.appliedProcessing = self.fc[fp]
            self.grayAdjustZone = self.fc[fp + 1]
            self.backgroundvalue = int.from_bytes(
                self.fc[fp + 2 : fp + 4], byteorder="little", signed=False
            )
            self.desiredRendering = self.fc[fp + 4]
            self.desired_rotation_fraction = self.fc[fp + 5]
            self.rendering_argShort = int.from_bytes(
                self.fc[fp + 6 : fp + 8], byteorder="little"
            )
            self.rendering_argFloat = struct.unpack("f", self.fc[fp + 8 : fp + 12])[0]
            self.desired_rotation = int.from_bytes(
                self.fc[fp + 12 : fp + 14], byteorder="little"
            )
            self.rotaion_offset = int.from_bytes(
                self.fc[fp + 14 : fp + 16], byteorder="little"
            )
            # spare 4
        else:
            self.hasLEEMData = False
            voidNr = int(0)
            self.LEEMData = struct.unpack("240c", "\x00" * 240)
            self.appliedProcessing = b""
            self.grayAdjustZone = b""
            self.backgroundvalue = voidNr
            self.desiredRendering = b""
            # spare 1
            self.rendering_argShort = voidNr
            self.rendering_argFloat = 0.0
            self.desired_rotation = voidNr
            self.rotaion_offset = voidNr

        if verbose:
            print("imageHeadersize = " + str(self.imageHeadersize))
            print("version = " + str(self.version))
            print("colorScaleLow = " + str(self.colorScaleLow))
            print("colorScaleHigh = " + str(self.colorScaleHigh))
            print("imageTime = " + str(self.imageTime))
            print("maskXShift = " + str(self.maskXShift))
            print("maskYShift = " + str(self.maskYShift))
            print("rotateMask = " + str(self.rotateMask))
            print("attachedMarkupSize = " + str(self.attachedMarkupSize))
            print("hasAttachedMarkup = " + str(self.hasAttachedMarkup))
            print("spin = " + str(self.spin))
            print("LEEMDataVersion = " + str(self.LEEMDataVersion))

    def leemParameters(self, verbose=False) -> None:
        """Loads the image parameters from header"""
        startPos = self.headerSize + self.imageHeadersize + self.attachedMarkupSize
        endPos = startPos + self.LEEMDataVersion + 1
        self.leemData = self.fc[startPos:endPos]
        print(self.leemData)
        # endLeemData = endPos-startPos
        # zeroPos = (i for i, e in enumerate(self.leemData) if e == 0)
        # self.zeroList = []
        # nx = next(zeroPos,-1)
        # while nx > 0:
        #     self.zeroList.append(nx)
        #     nx = next(zeroPos,-1)
        # endLeemData = self.zeroList[-1]
        # self.paramList = []
        # endPos = 0
        # while endPos <= endLeemData:
        #     res, endPos = self.extractLeemParam(endPos)
        #     self.paramList.append(res)

    def getUnits(self, val) -> str:
        """Returns the units according to page 10 of the "FileFormats 2017" specifications"""
        return {
            "0": "none",
            "1": "V",
            "2": "mA",
            "3": "A",
            "4": "C",
            "5": "K",
            "6": "mV",
            "7": "pA",
            "8": "nA",
            "9": "uA",
        }.get(val, "none")

    def extractLeemParam(self, startPos) -> dict:
        """Extracts the dictionary of a specific parameter starting at startPos"""
        # device = {'number':0, 'name':'', 'units':'', 'value':0}
        devNr = self.leemData[startPos] & 0x7F  # removed the first bit!
        if devNr < 100:
            # normal device
            endName = self.zeroList[bs.bisect_left(self.zeroList, startPos + 1)]
            device = {"number": 0, "name": "", "units": "", "value": 0}
            device["number"] = int(devNr)
            device["name"] = bytes(self.leemData[startPos + 1 : endName - 1]).decode(
                "utf-8"
            )
            device["units"] = self.getUnits(
                bytes(self.leemData[endName - 1 : endName]).decode("utf-8")
            )
            endVal = endName + 5
            device["value"] = struct.unpack(
                "f", self.leemData[endName + 1 : endName + 5]
            )[0]
            return device, endVal
        elif devNr == 100:
            # Mitutoyo micrometer readout
            device = {"number": 0, "name": "Mitutoyo_x", "units": "mm", "value": ""}
            device["number"] = int(devNr)
            valX = struct.unpack("f", self.leemData[startPos + 1 : startPos + 5])[0]
            valY = struct.unpack("f", self.leemData[startPos + 5 : startPos + 9])[0]
            device["value"] = str(valX) + "," + str(valY)
            endPos = startPos + 9
            return device, endPos
        elif devNr == 101:
            # FOV
            print("Old FoV")
            print("############################################")
            print("### NOT TESTED - device 101 - NOT TESTED ###")
            print("############################################")
            endName = self.zeroList[bs.bisect_left(self.zeroList, startPos + 1)]
            device = {"number": 0, "name": "", "units": "", "value": 0}
            device["number"] = int(devNr)
            device["name"] = "FOV=" + bytes(
                self.leemData[startPos + 1 : endName - 1]
            ).decode("utf-8")
            endVal = endName + 4
            device["value"] = struct.unpack(
                "f", self.leemData[endName + 1 : endName + 5]
            )[0]
            return device, endVal
        elif devNr == 102:
            # Varian controller #1
            print("Varian controller #1")
            print("############################################")
            print("### NOT TESTED - device 102 - NOT TESTED ###")
            print("############################################")
        elif devNr == 103:
            # Varian controller #2
            print("Varian controller #2")
            print("############################################")
            print("### NOT TESTED - device 103 - NOT TESTED ###")
            print("############################################")
        elif devNr == 104:
            # Camera exposure
            device = {"number": 0, "name": "", "units": "", "value": 0}
            device["number"] = int(devNr)
            device["units"] = "seconds"
            device["value"] = struct.unpack(
                "f", self.leemData[startPos + 1 : startPos + 5]
            )[0]
            b1 = self.leemData[startPos + 5]
            b2 = self.leemData[startPos + 6]
            if b1 == 255:
                avgType = "(sliding average)"
            elif b1 == 0:
                avgType = "(average off)"
            else:
                avgType = "(average " + str(b2) + " images)"
            device["name"] = "Camera exposure " + avgType
            endPos = startPos + 7
            return device, endPos
        elif devNr == 105:
            # Title
            endName = self.zeroList[bs.bisect_left(self.zeroList, startPos + 1)]
            if endName == startPos + 1:
                device = {
                    "number": int(devNr),
                    "name": "Title",
                    "units": "none",
                    "value": "",
                }
                endVal = startPos + 2
            else:
                device = {
                    "number": int(devNr),
                    "name": "Title",
                    "units": "none",
                    "value": bytes(self.leemData[startPos + 1 : endName]).decode(
                        "utf-8"
                    ),
                }
                endVal = endName
            return device, endVal
        elif (devNr >= 106) and (devNr <= 109):
            device = {"number": 0, "name": "", "units": "", "value": 0}
            device["number"] = int(devNr)
            endName = self.zeroList[bs.bisect_left(self.zeroList, startPos)]
            device["name"] = bytes(self.leemData[startPos + 1 : endName]).decode(
                "utf-8"
            )
            endUnits = self.zeroList[bs.bisect_left(self.zeroList, endName + 1)]
            device["units"] = bytes(self.leemData[endName + 1 : endUnits]).decode(
                "utf-8"
            )
            device["value"] = struct.unpack(
                "f", self.leemData[endUnits + 1 : endUnits + 5]
            )[0]
            endPos = endUnits + 5
            return device, endPos
        elif devNr == 110:
            # FoV
            endName = self.zeroList[bs.bisect_left(self.zeroList, startPos + 1)]
            device = {"number": 0, "name": "", "units": "", "value": 0}
            device["number"] = int(devNr)
            fov = self.leemData[startPos + 1 : endName]
            if 181 in fov:
                pos = fov.index(181)
                device["name"] = (
                    "FOV="
                    + bytes(fov[0:pos]).decode("utf-8")
                    + "\u03BC"
                    + bytes(fov[pos + 1 : -1]).decode("utf-8")
                )
            else:
                device["name"] = "FOV=" + bytes(fov).decode("utf-8")
            endVal = endName + 5
            device["value"] = struct.unpack(
                "f", self.leemData[endName + 1 : endName + 5]
            )[0]
            return device, endVal
        elif devNr == 111:
            # PhiTheta
            print("Phi/Theta")
            print("############################################")
            print("### NOT TESTED - device 111 - NOT TESTED ###")
            print("############################################")
        elif devNr == 112:
            # Spin
            print("Spin")
            print("############################################")
            print("### NOT TESTED - device 112 - NOT TESTED ###")
            print("############################################")
        elif devNr == 113:
            # FoV Rotation (from LEEM presets)
            device = {
                "number": 0,
                "name": "FOV rotation (from LEEM presets)",
                "units": "deg",
                "value": 0,
            }
            device["number"] = int(devNr)
            valX = struct.unpack("f", self.leemData[startPos + 1 : startPos + 5])[0]
            device["value"] = str(valX)
            endPos = startPos + 5
            return device, endPos
        elif devNr == 114:
            # Mirror state
            device = {
                "number": 0,
                "name": "Mirror state",
                "units": "Mirror",
                "value": 0,
            }
            device["number"] = int(devNr)
            valX = int.from_bytes(
                self.leemData[startPos + 1 : startPos + 3], byteorder="little"
            )
            device["value"] = str(valX)
            endPos = startPos + 3
            return device, endPos
        elif devNr == 115:
            # MCP screen voltage in kV
            device = {"number": 0, "name": "ScreenVoltage", "units": "kV", "value": 0}
            device["number"] = int(devNr)
            valX = struct.unpack("f", self.leemData[startPos + 1 : startPos + 5])[0]
            device["value"] = str(valX)
            endPos = startPos + 5
            return device, endPos
        elif devNr == 116:
            # MCP channelplate voltage in kV
            device = {"number": 0, "name": "ChannelPlate", "units": "kV", "value": 0}
            device["number"] = int(devNr)
            valX = struct.unpack("f", self.leemData[startPos + 1 : startPos + 5])[0]
            device["value"] = str(valX)
            endPos = startPos + 5
            return device, endPos
        # elif (devNr >= 120) and (devNr <= 130):
        # additional gauges
        # print("additional gauges")
        return 0, startPos


def load_all_images(folder: "Path") -> list:
    ru = ReadUView()
    images = []
    for file in os.listdir(folder):
        if file.endswith(".dat"):
            images.append(ru.getImage(folder / file))

    return images

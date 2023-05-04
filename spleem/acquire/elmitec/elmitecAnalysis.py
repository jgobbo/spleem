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

# import readUview as ru
from .readuview import readUview as ru
import matplotlib.pyplot as plt
from skimage import exposure


class imgStackClass:
    def __init__(self, fn) -> None:
        """Initializes the imgStackClass object"""
        # fn must be a list of file names to load as a numpy array
        if len(fn) < 1:
            print("Failed. No file loaded")
            return
        try:
            self.imageWidth = 0
            self.imageHeight = 0
            self.nImages = len(fn)
            for f in fn:
                ind = fn.index(f)
                if ind == 0:
                    ruObj = ru.readUviewClass()
                    img = ruObj.getImage(f)
                    self.imgType = img.dtype.name
                    self.imageWidth = ruObj.imageWidth
                    self.imageHeight = ruObj.imageHeight
                    self.stack = np.zeros(
                        (self.nImages, self.imageWidth, self.imageHeight),
                        dtype=np.ndarray,
                    )
                    self.stack[0] = img
                    self.limits = np.percentile(img, (2, 98))
                    #                    print("Loading image nr=%04i" %ind, end='\r')
                    print(f"\rLoading image nr=" + str("%04i" % ind), end="")
                    sys.stdout.flush()
                else:
                    img = ruObj.getImage(f)
                    self.imageWidth = ruObj.imageWidth
                    self.imageHeight = ruObj.imageHeight
                    try:
                        self.stack[ind] = img
                        #                        print("Loading image nr=%04i" %ind, end='\r')
                        print(f"\rLoading image nr=" + str("%04i" % ind), end="")
                        sys.stdout.flush()
                    except:
                        raise Exception("Error loading image nr".format(fn.index(f)))
            print("\n")
            self.current = 0
            self.fn = fn
            self.rawfn = []
            for f in fn:
                self.rawfn.append(os.path.basename(os.path.abspath(f)) + ".dat")
            self.dir = os.path.dirname(os.path.abspath(self.fn[0]))
        except:
            print("Loading of images failed")
            return

    def getImage(self, pos=-1) -> np.ndarray:
        if pos < 0:
            pos = self.current
        try:
            return self.stack[pos].astype(self.imgType)
        except:
            raise Exception("Index not valid or stack not yet defined")

    def getLimits(self, pos=-1, clip=2) -> tuple:
        if pos < 0:
            pos = self.current
        try:
            self.limits = np.percentile(self.getImage(pos), (clip, 100 - clip))
            return self.limits
        except:
            raise Exception("Index not valid or stack not yet defined")

    def getDrawImage(self, pos=-1, clip=2) -> np.ndarray:
        if pos < 0:
            pos = self.current
        if clip != 2:
            limits = np.percentile(self.getImage(pos), (2, 98))
        else:
            limits = self.limits
        try:
            img = exposure.rescale_intensity(
                self.stack[pos].astype(self.imgType), in_range=(limits[0], limits[1])
            )
            return img
        # .astype(self.imgType)
        except:
            raise Exception("Index not valid or stack not yet defined")

    def __repr__(self):
        try:
            outStr = [str("nImages = %04i" % self.nImages)]
            outStr.append(str("First image = %s" % self.rawfn[0]))
            outStr.append(str("Last image = %s" % self.rawfn[-1]))
            outStr.append(str("Directory = %s" % self.dir))
            outStr.append(
                str("Image size = (%i,%i)" % (self.imageWidth, self.imageHeight))
            )
            return "\n".join(outStr)
        except AttributeError:
            return "Object not defined"


class elmitecAnalysisClass:
    def __init__(self) -> None:
        """Initializes the elmitecAnalysisClass object"""

    def __repr__(self):
        try:
            outStr = [str("nImages = %04i" % self.imgStack.nImages)]
            outStr.append(str("First image = %s" % self.imgStack.fn[0]))
            outStr.append(str("Last image = %s" % self.imgStack.fn[-1]))
            outStr.append(str("Directory = %s" % self.imgStack.dir))
            outStr.append(
                str("Image size = (%i,%i)" % (self.imageWidth, self.imageHeight))
            )
            return "\n".join([outStr])
        except AttributeError:
            return "Object not defined"

    def loadDir(self, dirName):
        self.dir = dirName


import os


def getDatFilesInDir(mypath=r"K:\Data\TurningPointResolution"):
    fileList = []
    for file in os.listdir(mypath):
        if file.endswith(".dat"):
            fileList.append(os.path.join(mypath, file))
    return fileList


# Run examples
fn = getDatFilesInDir()
stack = imgStackClass(fn)


# import pylab as pl
# from IPython import display
# from IPython import get_ipython
# get_ipython().run_line_magic('matplotlib', 'qt5')

# limits= stack.getLimits(pos=0,clip=2)
##imgObj = plt.imshow(stack.getImage(0), cmap=plt.cm.gray, vmin=limits[0], vmax=limits[1])
# fig,ax = plt.subplots(1,1)
# ax.imshow(stack.getImage(0), cmap=plt.cm.gray, vmin=limits[0], vmax=limits[1])
# fig.canvas.draw()
# ax.imshow(stack.getImage(1), cmap=plt.cm.gray, vmin=limits[0], vmax=limits[1])

# image = sitk.GetImageFromArray(stack.getImage(1), isVector=True)


import tkinter as tk
from tkinter import filedialog
import PIL.Image, PIL.ImageTk
import PIL.ImageOps

# import cv2
from skimage.transform import rescale
from skimage import exposure


class elmitecImageViewer:
    def __init__(self, stack):
        imgNr = 0
        self.winSize = (1024, 1024)
        self.winPadding = (100, 200)
        self.stack = stack
        self.root = tk.Tk()
        self.mainFrame = tk.Frame(
            self.root,
            height=self.winSize[0] + self.winPadding[0],
            width=self.winSize[1] + self.winPadding[1],
            bg="white",
        )
        self.mainFrame.pack()
        self.topFrame = tk.Frame(self.mainFrame, height=100, width=200, bg="white")
        self.topFrame.pack(fill=tk.X)
        self.listbox = tk.Listbox(self.mainFrame)
        self.listbox.pack(side=tk.LEFT, fill=tk.Y)
        self.listbox.bind("<<ListboxSelect>>", self.selectList)
        self.imageCanvas = tk.Canvas(
            self.mainFrame, height=self.winSize[0], width=self.winSize[0], bg="orange"
        )
        self.imageCanvas.pack(side=tk.RIGHT, expand=True)
        self.mainFrame.winfo_toplevel().title("Image number %04i" % imgNr)

        for n, item in enumerate(self.stack.fn):
            self.listbox.insert(tk.END, "{:04d} - {}".format(n, os.path.basename(item)))
        openButton = tk.Button(self.topFrame, text="Open", command=self.openImageList)
        openButton.grid(row=0, column=0, pady=20)
        prevButton = tk.Button(self.topFrame, text="Previous")
        prevButton.grid(row=0, column=2, pady=20)
        nextButton = tk.Button(self.topFrame, text="Next")
        nextButton.grid(row=0, column=1, pady=20)

        img = self.stack.getImage(imgNr)
        p2, p98 = np.percentile(img, (2, 98))
        img_rescale_int = exposure.rescale_intensity(
            img, in_range=(p2, p98), out_range=(0, 255)
        )
        intensityFixedImg = PIL.Image.fromarray(img_rescale_int)
        self.photo = PIL.ImageTk.PhotoImage(intensityFixedImg, master=self.root)

        self.imageOnCanvas = self.imageCanvas.create_image(
            0, 0, image=self.photo, anchor=tk.NW
        )
        self.listbox.selection_clear(0, last=self.stack.nImages - 1)
        self.listbox.selection_set(0)
        self.windowRunning = True
        self.root.mainloop()
        self.windowRunning = False

    def showImage(self, imgNr=-1):
        if not self.windowRunning:
            return
        current = self.stack.current
        if imgNr >= 0:
            current = imgNr
        img = self.stack.getImage(current)
        if (self.stack.imageWidth > self.winSize[0]) or (
            self.stack.imageHeight > self.winSize[1]
        ):
            rescaleFactorX = self.winSize[0] / self.stack.imageWidth
            rescaleFactorY = self.winSize[1] / self.stack.imageHeight
            rescaleFactor = min(rescaleFactorX, rescaleFactorY)
            img = rescale(img, rescaleFactor, preserve_range=True)
        p2, p98 = np.percentile(img, (2, 98))
        img_rescale_int = exposure.rescale_intensity(
            img, in_range=(p2, p98), out_range=(0, 255)
        )
        intensityFixedImg = PIL.Image.fromarray(img_rescale_int)
        self.photo = PIL.ImageTk.PhotoImage(intensityFixedImg, master=self.root)
        self.imageCanvas.itemconfig(self.imageOnCanvas, image=self.photo)

    def selectList(self, evt):
        w = evt.widget
        index = int(w.curselection()[0])
        value = w.get(index)
        self.stack.current = index
        if self.stack.current < 0:
            self.stack.current = 0
        if self.stack.current > self.stack.nImages - 1:
            self.stack.current = self.stack.nImages - 1
        self.showImage()
        self.updateTitle(value)

    def updateTitle(self, value=""):
        self.mainFrame.winfo_toplevel().title(
            "Image number %04i (%s)"
            % (self.stack.current, os.path.basename(self.stack.fn[self.stack.current]))
        )

    def openImageList(self):
        filenames = list(
            tk.filedialog.askopenfilenames(
                title="Select files",
                filetypes=(("uView", "*.dat"), ("Tiff files", "*.tif")),
            )
        )
        print(type(filenames))
        self.stack = imgStackClass(filenames)
        self.listbox.delete(0, tk.END)
        for n, item in enumerate(self.stack.fn):
            self.listbox.insert(tk.END, "{:04d} - {}".format(n, os.path.basename(item)))
        self.listbox.selection_set(0)
        self.showImage(0)


imgViewer = elmitecImageViewer(stack)
imgViewer.showImage()

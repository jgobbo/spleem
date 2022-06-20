# -*- coding: utf-8 -*-
"""
Copyright 2019 Dr. Helder Marchetto
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import readUview as ru
import matplotlib.pyplot as plt

fn = r'C:\Insert\Your\Path\To\Your\File\Here\myFile.dat'

ruObj = ru.readUviewClass()
img = ruObj.getImage(fn)

#show the image
plt.imshow(img, cmap=plt.cm.gray)

#show the image parameter list
for p in ruObj.paramList:
    print(p)



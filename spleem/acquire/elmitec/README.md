# ElmitecPython

These procedures are meant for users of Elmitec Elektronenmikroskopie GmbH users.

You will find the following objects available:

**readUview**:

   This object can be installed as a package (see instructions below) and confortably used as an object to read .dat files produced with Uview.
   You will also need (not just for executing these procedures) numpy and matplotlib. Install these using the recommended method for anaconda (which is not using PIP).
   
   Disclaimer: Not all versions have been tested. I reading of an image file fails, please try modifying the procedure yourself or send me the file and I will try to fix the problem. Generally, some bugs are only found when testing real life data.

**elmitecConnect**:

   This object allows to connect to a local or remote machine control imaging parameters (LEEM2000 devices) and image acquisition (UView)
   Open the elmitecConnect.py file and run it.
   Then you can initiate an "elmitecConnect" object as follows:

```python
>>> import elmitecConnect as ec
>>> oec = ec.elmitecConnect()
Connect with ip=192.168.178.26, LEEMport=5566, UVIEWport=5570
Connect with ip=192.168.178.26, port=5566
connecting leem with
192.168.178.26
5566
Connected. 90 modules found 
#########################################
To see which devices are available, type:
for i in oLeem.Modules.values(): print(i)
for i in oLeem.Mnemonic.values(): print(i)
#########################################
To check the value of a device, type:
print(oLeem.getValue('FL')
Connect with ip=192.168.178.26, port=5570
>>>oec.oLeem.getValue('FL')
2960.0
>>>oec.oUview.getROI()
[0, 0, 1600, 1200]
>>>
```

You can change IP and port in the opening statement by calling 
```python
>>>oec = ec.elmitecConnect(ip='192.168.178.26', LEEMport=5566, UVIEWport=5570)
```

**elmitecAnalysis**:

This is an early attempt at analysing Elmitec data with Python. Installation of an extra package is required: scikit-image
Further input is very welcome!

For any questions please contact Helder Marchetto @ Elmitec.

If you wish to contribute, you are very welcome.

Helder

# Instruction for installing (Elmitec) packages

Download the file readUview-1.0.tar.gz (or the latest available version)
Open Anaconda navigator, select the environment and open a terminal:

![Open terminal](/images/openTerminal.jpg)

Once the terminal is open type (and use the appropriate path to the file you just downloaded!!!):

pip install C:\Users\helder\Downloads\readUview-1.0.tar.gz

![PIP install](/images/pipInstall.jpg)





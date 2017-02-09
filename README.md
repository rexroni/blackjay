# blackjay
Like a blue jay, but sneakier...

## Features
Blackjay is a multi-platform, encrypted file-syncing program:
* The blackjay client watches a folder (the local store) for file changes
* Updated files are encrypted with Blowfish CBC encryption and sent to server over SSH
* A blackjay server has no access the original data\*
* Additional blackjay clients sync, decrypt, and validate, then sync their own changes

Blackjay is:
* Simple: less than 1000 lines of python
* Smart: Synchronization conflicts are reliably identified for the user to correct
* Secure\*\*: Unencrypted only exists on trusted devices, SSH is used for all communications.
* Multiplatform: runs on Mac, Windows, and Linux.
* Free: (un)licensed under the Unlicense

## dependencies
* python 3.6
* watchdog - notifies applications when files change in folder
* pycrypto - for encrypting your files (files are never stored or trasmitted to server in plaintext)
* sshtunnel - for encrypting your connection with the server and providing authentication to the server through ssh using public/private keypairs

## windows client install step by step (tested on windows 7)
1. Download Python 3.6 ( https://www.python.org/ftp/python/3.6.0/python-3.6.0.exe )
+ Install Python 3.6 ( defaults to C:\Users\{USERNAME}\AppData\Local\Programs\Python\Python36-32 )
  + Check box for Add Python 3.6 to PATH
+ Install Visual C++ 2015 Build Tools ( http://landinghub.visualstudio.com/visual-cpp-build-tools )
+ Open cmd.exe ( Press Windows key and type cmd.exe )
+ Force stdint.h in Enviroment Variables ( http://stackoverflow.com/questions/41843266/microsoft-windows-python-3-6-pycrypto-installation-error )
  + I had to open a command prompt with administrative prilegeses (right click on cmd.exe, select "Run as Administrator") and give it this command:
  + > CL=-FI"C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\stdint.h"
  + This step was required by errors like: "eror C2061: syntax error: identifier 'intmax\_t'" when I did the pip install on the next step
  + You might have to look for the path to stdint.h on your system by opening windows explorer and searching for it and put that in the above command.
+ Run the command in the same command prompt to install python library dependencies
  + > pip install watchdog pycrypto sshtunnel
+ Download our project from https://github.com/rexroni/blackjay/tree/dev (Green button on right "Clone or download" -> "Download ZIP")

##\* Future Plans:
* Currently, only the file data is encrypted.  "Envelope" information, such as the filename, modification time, or file size, are readily visible on the server, but in future versions blackjay hopes to offer even more privacy.  Even now, full privacy can be secured by running the server on a local machine, even a Raspberry PI
* Many non-security design decisions were made in order to have a functional application, instead of a perfect application.  Future versions of blackjay will be more resource efficient.

##\*\* WARNING:
This software is alpha software; it should not be considered complete, or even secure.  As much as possible, blackjay tries to use respected, open-source libraries to handle encryption details, such as the exclusive use of communication through SSH tunnels or encrypting files with the PyCrypto library.  Use Blackjay at your own risk, and if you find any security holes, for Pete's sake, let us know.

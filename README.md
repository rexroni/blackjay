# blackjay
Like a blue jay, but sneakier...

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
  + This step was required by errors like: "eror C2061: syntax error: identifier 'intmax_t'" when I did the pip install on the next step
  + You might have to look for the path to stdint.h on your system by opening windows explorer and searching for it and put that in the above command.
+ Run the command in the same command prompt to install python library dependencies
  + > pip install watchdog pycrypto sshtunnel
+ Download our project from https://github.com/rexroni/blackjay/tree/dev (Green button on right "Clone or download" -> "Download ZIP")

## windows client/server local test
1. Open two cmd.exe windows and cd to the directory you extracted the project zip into
+ Create two folders
  + > mkdir client
  + > mkdir server
+ Run the client and server in each of the two cmd.exe windows:
  + > python client.py client
  + > python server.py server
+ Select all the defaults for the client config (localhost, 12345, password)  Password should be atleast 8 bits long but for testing it will just be saved into a config file and you won't have to edit it again.
+ Test that you can place files in the client directory and edit them and the changes sync into the server directory correctly.
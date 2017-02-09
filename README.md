# blackjay
Like a blue jay, but sneakier...

## dependencies
python 3.6
watchdog - notifies applications when files change in folder
pycrypto - for encrypting your files (files are never stored or trasmitted to server in plaintext)
sshtunnel - for encrypting your connection with the server and providing authentication to the server through ssh using public/private keypairs

## windows client install step by step
1. Download Python 3.6 ( https://www.python.org/ftp/python/3.6.0/python-3.6.0.exe )
2. Install Python 3.6 ( defaults to C:\Users\{USERNAME}\AppData\Local\Programs\Python\Python36-32 )
2.1 Check box for Add Python 3.6 to PATH
3. Install Visual C++ 2015 Build Tools ( http://landinghub.visualstudio.com/visual-cpp-build-tools )
4. Open cmd.exe ( Press Windows key and type cmd.exe )
5. Force stdint.h in Enviroment Variables ( http://stackoverflow.com/questions/41843266/microsoft-windows-python-3-6-pycrypto-installation-error )
5.1 I had to open a command prompt with administrative prilegeses (right click on cmd.exe, select "Run as Administrator") and give it this command:
> CL=-FI"C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\stdint.h"
because of errors like: eror C2061: syntax error: identifier 'intmax_t' when I ran the next step
You might have to look for the path to stdint.h on your system by opening windows explorer and searching for it and put that in the above command.
6. Run the command in the same command prompt to install python library dependencies
> pip install watchdog pycrypto sshtunnel
7. Download our project from https://github.com/rexroni/blackjay/tree/dev (Green "Clone or download" -> "Download ZIP")


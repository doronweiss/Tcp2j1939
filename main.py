import os
from mctcpserver import mctcpserver

mts = mctcpserver('127.0.0.1', 65432)
mts.run()
# AB3GY WSJT-X Interface Utilities 
A set of Python classes used to interface with the WSJT-X application over a UDP connection.

Developed for personal use by the author, but available to anyone under the license terms below.

WSJT-X home page: https://www.physics.princeton.edu/pulsar/k1jt/wsjtx.html

### wsjtxmon.py
Python class for monitoring and parsing WSJT-X messages over a UDP port.

Supports WSJT-X Version 2.2.0 and later.

WSJT-X message formats are described in the following WSJT-X source file:
  src/wsjtx/Network/NetworkMessage.hpp.

### QColor.py
Qt QColor emulation class used by wsjtxmon.py. Used by WSJT-X for callsign highlighting.


### FT8Decode.py
Class used for processing FT8 decoded messages from WSJT-X.

### Dependencies
Written for Python 3.x.

Requires `encode.py` and `decode.py` in the ab3gy-pyutils repository.

Repository: https://github.com/tkerr/ab3gy-pyutils
 
### Author
Tom Kerr AB3GY
ab3gy@arrl.net

### License
Released under the 3-clause BSD license.
See license.txt for details.

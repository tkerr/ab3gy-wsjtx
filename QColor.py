###############################################################################
# QColor.py
# Author: Tom Kerr AB3GY
#
# Qt QColor emulation class for Python.
# Provides a means to searialize and deserialize a QColor object for
# interfacing with applications that use Qt.  Written specifically for
# WSJT-X callsign highlighting in the wsjtxmon class.
#
# Designed for personal use by the author, but available to anyone under the
# license terms below.
###############################################################################

###############################################################################
# License
# Copyright (c) 2020 Tom Kerr AB3GY (ab3gy@arrl.net).
#
# Redistribution and use in source and binary forms, with or without 
# modification, are permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice,   
# this list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright notice,  
# this list of conditions and the following disclaimer in the documentation 
# and/or other materials provided with the distribution.
# 
# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without 
# specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE 
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
# POSSIBILITY OF SUCH DAMAGE.
###############################################################################

# Local packages.
import decode
import encode

##############################################################################
# Global objects and data.
##############################################################################


##############################################################################
# Functions.
##############################################################################

# ------------------------------------------------------------------------
def rgba_join(red, grn, blu, alpha=0xFF):
    """
    Join individual red, green, blue and alpha values into a composite
    RGBA value.
    
    Parameters
    ----------
    red : int
        The red value (0-255)
    grn : int
        The green value (0-255)
    blu : int
        The blue value (0-255)
    alpha : int
        The optional alpha value (0-255).  Set to 100% opaque (255)
        if not specified.
  
    Returns
    -------
    rgba : int
        A 32-bit composite RGBA value.
    """
    rgba = ((red & 0xFF) << 24) \
        + ((grn & 0xFF) << 16)  \
        + ((blu & 0xFF) << 8)   \
        + (alpha & 0xFF)
    return rgba

# ------------------------------------------------------------------------
def rgba_split(rgba):
    """
    Split a 32-bit RGBA value into its component parts.
    
    Parameters
    ----------
    rgba : int
        The 32-bit composite RGBA value to split.
  
    Returns
    -------
    (red, grn, blu, alpha) : tuple
        A tuple of individual red, green, blue and alpha values.
    """
    alpha = (rgba & 0xFF)
    rgba >>= 8
    blu = (rgba & 0xFF)
    rgba >>= 8
    grn = (rgba & 0xFF)
    rgba >>= 8
    red = (rgba & 0xFF)
    return (red, grn, blu, alpha)


##############################################################################
# QColor class.
##############################################################################

class QColor (object):
    """
    Qt QColor emulation class for Python.
    Provides a means to searialize and deserialize a QColor object for
    interfacing with applications that use Qt.
    This class serializes the color encoding as ARGB (alpha, red, green, blue).
    """
    # Qt color specification enumerated type.
    CSPEC_INVALID      = int(0)
    CSPEC_RGB          = int(1)
    CSPEC_HSV          = int(2)
    CSPEC_CMYK         = int(3)
    CSPEC_HSL          = int(4)
    CSPEC_EXTENDED_RGB = int(5)
    
    # Qt pre-defined color names.
    COLOR_BLACK        = int(2)
    COLOR_WHITE        = int(3)
    COLOR_DARK_GRAY    = int(4)
    COLOR_GRAY         = int(5)
    COLOR_LIGHT_GRAY   = int(6)
    COLOR_RED          = int(7)
    COLOR_GREEN        = int(8)
    COLOR_BLUE         = int(9)
    COLOR_CYAN         = int(10)
    COLOR_MAGENTA      = int(11)
    COLOR_YELLOW       = int(12)
    COLOR_DARK_RED     = int(13)
    COLOR_DARK_GREEN   = int(14)
    COLOR_DARK_BLUE    = int(15)
    COLOR_DARK_CYAN    = int(16)
    COLOR_DARK_MAGENTA = int(17)
    COLOR_DARK_YELLOW  = int(18)
    COLOR_TRANSPARENT  = int(19)
    
    # Additional color names not defined in Qt.
    COLOR_ORANGE       = int(20)
    COLOR_DARK_VIOLET  = int(21)
    
    # Not part of Qt spec.
    # An invalid color clears and cancels WSJT-X highlighting.
    COLOR_INVALID = int(255)  
    
    # ------------------------------------------------------------------------
    def __init__(self, *, name=None, rgba=None, alpha=0xFF):
        """
        Class constructor.
        
        Parameters
        ----------
        name : int
            An optional pre-defined color name to use as a means of
            initialization.  Use either name or rgba (or neither),
            but not both.
            
        rgba : int
            An optional 32-bit value to use as a means of
            initialization.  Use either name or rgba (or neither),
            but not both.
        
        Returns
        -------
        None
        """
        
        # Variable initialization.
        self.__version__ = str("0.1")  # Version per PEP 396
        self.cspec   = self.CSPEC_RGB  # Color spec is RGB
        self.red     = 0               # Default red value
        self.grn     = 0               # Default green value
        self.blu     = 0               # Default blue value
        self.alpha   = alpha & 0xFF    # Default alpha value
        self.pad     = 0               # Pad value (used only for CMYK color spec)
        self._endian = 'little'        # Assumes data is transferred in little endian format
        
        # Initialize a serialized byte array.
        self.array = bytearray(encode.byte(self.CSPEC_RGB, self._endian))

        if name is not None:
            # Optional initialization using a pre-defined color name.
            self.setByName(name, alpha=alpha)
        elif rgba is not None:
            # Optional initialization using a 32-bit color value.
            self.setByValue(rgba=rgba)

    # ------------------------------------------------------------------------
    def encode(self, red=-1, grn=-1, blu=-1, alpha=-1):
        """
        Encode a QColor as a byte array.
        All parameters are optional.  If not specified, then their previously
        set values will be used.
        
        Parameters
        ----------
        red : int
            The optional red color value (range = 0-255).
        grn : int
            The optional green color value (range = 0-255).
        blu : int
            The optional blue color value (range = 0-255).
        alpha : int
            The optional alpha value. Range is 0 (transparent) to 255 (opaqaue).
            Default = 255.
        
        Returns
        -------
        A bytearray containing the encoded data.
        """
        if (red >= 0): self.red = red & 0xFF
        if (grn >= 0): self.grn = grn & 0xFF
        if (blu >= 0): self.blu = blu & 0xFF
        if (alpha >= 0): self.alpha = alpha & 0xFF
        
        self.array = bytearray(encode.byte(self.cspec, self._endian))
        self.array.extend(encode.uword(self.alpha, self._endian))
        self.array.extend(encode.uword(self.red, self._endian))
        self.array.extend(encode.uword(self.grn, self._endian))
        self.array.extend(encode.uword(self.blu, self._endian))
        self.array.extend(encode.uword(self.pad, self._endian))
        return self.array
        
        
    # ------------------------------------------------------------------------
    def decode(self, data):
        """
        Decode a serialized QColor stream and set the instance variables 
        cspec, red, grn, blu, alpha and pad accordingly.
        Note that values are not checked and may be invalid.
        
        Parameters
        ----------
        data : bytearray
            A data array containing the data stream to decode.
        
        Returns
        -------
        status : bool
            True if decoding was successful, False otherwise.  
            The instance variables cspec, red, grn, blu, alpha and pad are modified.
        """
        status = True
        index  = 0
        remain = len(data)
        
        if (remain >= 1):
            self.cspec = decode.byte(data[index:index+1], endian=self._endian)
            index += 1
            remain -= 1
        else: status = False
        
        if status & (remain >= 2):
            self.alpha = decode.uword(data[index:index+2], endian=self._endian)
            index += 2
            remain -= 2
        else: status = False
        
        if status & (remain >= 2):
            self.red = decode.uword(data[index:index+2], endian=self._endian)
            index += 2
            remain -= 2
        else: status = False
        
        if status & (remain >= 2):
            self.grn = decode.uword(data[index:index+2], endian=self._endian)
            index += 2
            remain -= 2
        else: status = False
        
        if status & (remain >= 2):
            self.blu = decode.uword(data[index:index+2], endian=self._endian)
            index += 2
            remain -= 2
        else: status = False
        
        if status & (remain >= 2):
            self.pad = decode.uword(data[index:index+2], endian=self._endian)
            index += 2
            remain -= 2
        else: status = False

        return status
        
        
    # ------------------------------------------------------------------------
    def setByName(self, name, *, alpha=-1):
        """
        Set the color using a pre-defined Qt color name.
        
        Parameters
        ----------
        name : int
            The pre-defined Qt color name (e.g., QColor.COLOR_DARK_GRAY)
        alpha : int
            Optional alpha value.  Set to fully opaque (255) if not specified.
            Exception: QColor.TRANSPARENT always sets the alpha value to fully transparent (0).
        
        Returns
        -------
        None
        """
        # Force color spec to RGB and pad to zero.
        self.cspec = self.CSPEC_RGB
        self.pad = 0
        
        # Set the alpha value.
        if (alpha >= 0):
            self.alpha = alpha
        else:
            self.alpha = 0xFF
        
        # Set the color by name.
        if (name == self.COLOR_BLACK):
            self.red = 0x00
            self.grn = 0x00
            self.blu = 0x00
        elif (name == self.COLOR_WHITE):
            self.red = 0xFF
            self.grn = 0xFF
            self.blu = 0xFF
        elif (name == self.COLOR_DARK_GRAY):
            self.red = 0x80
            self.grn = 0x80
            self.blu = 0x80
        elif (name == self.COLOR_GRAY):
            self.red = 0xA0
            self.grn = 0xA0
            self.blu = 0xA4
        elif (name == self.COLOR_LIGHT_GRAY):
            self.red = 0xC0
            self.grn = 0xC0
            self.blu = 0xC0
        elif (name == self.COLOR_RED):
            self.red = 0xFF
            self.grn = 0x00
            self.blu = 0x00
        elif (name == self.COLOR_GREEN):
            self.red = 0x00
            self.grn = 0xFF
            self.blu = 0x00
        elif (name == self.COLOR_BLUE):
            self.red = 0x00
            self.grn = 0x00
            self.blu = 0xFF
        elif (name == self.COLOR_CYAN):
            self.red = 0x00
            self.grn = 0xFF
            self.blu = 0xFF
        elif (name == self.COLOR_MAGENTA):
            self.red = 0xFF
            self.grn = 0x00
            self.blu = 0xFF
        elif (name == self.COLOR_YELLOW):
            self.red = 0xFF
            self.grn = 0xFF
            self.blu = 0x00
        elif (name == self.COLOR_DARK_RED):
            self.red = 0x80
            self.grn = 0x00
            self.blu = 0x00
        elif (name == self.COLOR_DARK_GREEN):
            self.red = 0x00
            self.grn = 0x80
            self.blu = 0x00
        elif (name == self.COLOR_DARK_BLUE):
            self.red = 0x00
            self.grn = 0x00
            self.blu = 0x80
        elif (name == self.COLOR_DARK_CYAN):
            self.red = 0x00
            self.grn = 0x80
            self.blu = 0x80
        elif (name == self.COLOR_DARK_MAGENTA):
            self.red = 0x80
            self.grn = 0x00
            self.blu = 0x80
        elif (name == self.COLOR_DARK_YELLOW):
            self.red = 0x80
            self.grn = 0x80
            self.blu = 0x00
        elif (name == self.COLOR_ORANGE):
            self.red = 0xFF
            self.grn = 0xA5
            self.blu = 0x00    
        elif (name == self.COLOR_DARK_VIOLET):
            self.red = 0x94
            self.grn = 0x00
            self.blu = 0xD3    
        elif (name == self.COLOR_TRANSPARENT):
            self.red   = 0x00
            self.grn   = 0x00
            self.blu   = 0x00
            self.alpha = 0x00 # Set alpha to transparent
        elif (name == self.COLOR_INVALID):
            self.cspec = self.CSPEC_INVALID
            self.red   = 0xFFFF
            self.grn   = 0xFFFF
            self.blu   = 0xFFFF
            self.alpha = 0xFFFF
            
            
    # ------------------------------------------------------------------------
    def setByValue(self, red=-1, grn=-1, blu=-1, *, alpha=-1, rgba=None):
        """
        Set the color using individual RGBA values or a composite RGBA value.
        
        Parameters
        ----------
        red : int
            The red value to use (0 - 255). Ignored if rgba is specified.
        grn : int
            The green value to use (0 - 255). Ignored if rgba is specified.
        blu : int
            The blue value to use (0 - 255). Ignored if rgba is specified.
        alpha : int
            The optional alpha value to use (0 - 255). Uses the existing value
            if not specified. Ignored if rgba is specified.
        
        Returns
        -------
        None
        """
        # Force color spec to RGB and pad to zero.
        self.cspec = self.CSPEC_RGB
        self.pad   = 0
        
        # RGBA value overrides everything.
        if rgba is not None:
            (self.red, self.grn, self.blu, self.alpha) = rgba_split(rgba)
        else:
            # Set the alpha value.
            if (alpha >= 0): self.alpha = alpha & 0xFF

            # Set the color and alpha values.
            if (red >= 0): self.red = red & 0xFF
            if (grn >= 0): self.grn = grn & 0xFF
            if (blu >= 0): self.blu = blu & 0xFF


###############################################################################
# Main program.
# Quick smoke test of QColor methods.
###############################################################################

if __name__ == "__main__":
    
    qc = QColor()
    
    red = 1
    grn = 2
    blu = 3
    alpha = 4
    
    print()
    print("rgba_join() and rgba_split() test")
    print("Joining R=" + str(red) + ",G=" + str(grn) + ",B=" + str(blu) + ",A=" + str(alpha))
    rgba = rgba_join(red, grn, blu, alpha)
    print("Joined rgba = #%08X" % rgba)
    (r, g, b, a) = rgba_split(rgba)
    print("Split R=" + str(r) + ",G=" + str(g) + ",B=" + str(b) + ",A=" + str(a))
    if (r == red) and (g == grn) and (b == blu) and (a == alpha):
        print("rgba_join() and rgba_split() passed.")
    else:
        print("rgba_join() and rgba_split() failed.")
    
    print()
    print("Encoding R=" + str(red) + ",G=" + str(grn) + ",B=" + str(blu) + ",A=" + str(alpha))
    data = qc.encode(red, grn, blu, alpha)
    print(data)
    if qc.decode(data):
        if (qc.red == red) and (qc.grn == grn) and (qc.blu == blu) and (qc.alpha == alpha):
            print("QColor.decode() passed.")
        else:
            print("QColor.decode() value match failed.")
    else:
        print("QColor.decode() failed.")
    
    print()
    red = 5
    grn = 6
    blu = 7
    alpha = 8
    print("Encoding R=" + str(red) + ",G=" + str(grn) + ",B=" + str(blu) + ",A=" + str(alpha))
    qc.setByValue(red, grn, blu, alpha=alpha)
    data = qc.encode()
    print(data)
    if qc.decode(data):
        if (qc.red == red) and (qc.grn == grn) and (qc.blu == blu) and (qc.alpha == alpha):
            print("QColor.decode() passed.")
        else:
            print("QColor.decode() value match failed.")
    else:
        print("QColor.decode() failed.")
    
    print()
    rgba = rgba_join(red, grn, blu, alpha)
    print("Encoding RGBA = #%08X" % rgba)
    qc.setByValue(rgba=rgba)
    data = qc.encode()
    print(data)
    if qc.decode(data):
        if (qc.red == red) and (qc.grn == grn) and (qc.blu == blu) and (qc.alpha == alpha):
            print("QColor.decode() passed.")
        else:
            print("QColor.decode() value match failed.")
    else:
        print("QColor.decode() failed.")
    
    print()
    print("Encoding QColor.COLOR_GRAY")
    qc.setByName(QColor.COLOR_GRAY)
    data = qc.encode()
    print(data)
    print("R=" + str(qc.red) + ",G=" + str(qc.grn) + ",B=" + str(qc.blu) + ",A=" + str(qc.alpha))
    
    print()
    print("Decoding QColor.COLOR_GRAY")
    if qc.decode(data):
        print("Success")
    else:
        print("Fail")
    print("R=" + str(qc.red) + ",G=" + str(qc.grn) + ",B=" + str(qc.blu) + ",A=" + str(qc.alpha))
    
    print()
    print("Encoding QColor.COLOR_INVALID")
    qc.setByName(QColor.COLOR_INVALID)
    data = qc.encode()
    print(data)
    print("R=" + str(qc.red) + ",G=" + str(qc.grn) + ",B=" + str(qc.blu) + ",A=" + str(qc.alpha))
    
    print()
    print("Initialization by name: QColor.DARK_MAGENTA")
    qc2 = QColor(name=QColor.COLOR_DARK_MAGENTA, alpha=127)
    print("R=" + str(qc2.red) + ",G=" + str(qc2.grn) + ",B=" + str(qc2.blu) + ",A=" + str(qc2.alpha))
       
    print()
    red = 0xAA
    grn = 0xBB
    blu = 0xCC
    alpha = 0xDD
    print("Initialization by RGBA: R=#%02X, G=#%02X, B=#%02X, A=#%02X" % (red, grn, blu, alpha))
    rgba = rgba_join(red, grn, blu, alpha)
    qc3 = QColor(rgba=rgba)
    print("R=#%02X, G=#%02X, B=#%02X, A=#%02X" % (qc3.red, qc3.grn, qc3.blu, qc3.alpha))
    
# End of file.

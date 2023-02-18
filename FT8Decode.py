###############################################################################
# FT8Decode.py
# Author: Tom Kerr AB3GY
#
# FT8Decode class used for processing of FT8 decoded messages from WSJT-X.
#
# Designed for personal use by the author, but available to anyone under the
# license terms below.
###############################################################################

###############################################################################
# License
# Copyright (c) 2022 Tom Kerr AB3GY (ab3gy@arrl.net).
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

# System level packages.
import sys
from operator import attrgetter

# Local packages.
from wsjtxmon import wsjtxmon

##############################################################################
# FT8Decode class.
##############################################################################

class FT8Decode(object):
    """
    FT8Decode class used for processing of FT8 decoded messages from WSJT-X.
    """

    # ------------------------------------------------------------------------
    def __init__(self, msg=[]):
        """
        Class constructor.
    
        Parameters
        ----------
        msg : list
            An optional wsjtxmon MSG_DECODE message used to initialize this object.
            See wsjtxmon.py for details.
        
        Returns
        -------
        None.
        """
        self.classname = type(self).__name__
        
        # WSJT-X decode message parameters.
        self.id_str   = ''
        self.new      = 0
        self.time_str = ''
        self.time     = 0
        self.snr_str  = ''
        self.snr      = 0
        self.dt_str   = ''
        self.dt       = 0
        self.df_str   = ''
        self.df       = 0
        self.mode_str = ''
        self.msg_str  = ''
        self.low_conf = 0
        self.off_air  = 0
        
        self.qrm   = 0.0  # Adjacent signal interference value (QRM)
        self.qrm_o = 0.0  # QRM with SNR offset
        self.esnr  = 0.0  # Effective SNR (with QRM factored in)
        self.nsig  = 0    # Number of interfering signals
        
        self.Reply = bytearray(0) # WSJT-X reply message
        
        msg_len = len(msg)
        if (msg_len > 0):
            if (msg[0] == wsjtxmon.MSG_DECODE):
                if (msg_len >= 11):
                    self.id_str   = str(msg[1])
                    self.new      = int(msg[2])
                    self.time_str = str(msg[3])
                    self.time     = int(msg[3])
                    self.snr_str  = str(msg[4])
                    self.snr      = int(msg[4])
                    self.dt_str   = str(msg[5])
                    self.dt       = float(msg[5])
                    self.df_str   = str(msg[6])
                    self.df       = int(msg[6])
                    self.mode_str = str(msg[7])
                    self.msg_str  = str(msg[8])
                    self.low_conf = int(msg[9])
                    self.off_air  = int(msg[10])
                else:
                    print(self.classname + ': Invalid decode message length.')
            else:
                print(self.classname + ': Invalid decode message initializer.')

    # ------------------------------------------------------------------------
    def __repr__(self):
        """
        Return the printable representation of the FT8Decode object.
        """
        return self.__str__()

    # ------------------------------------------------------------------------
    def __str__(self):
        """
        Stringify the FT8Decode object for printing.
        """
        my_list = self.tolist()
        my_str = '[' 
        for val in my_list:
            my_str += str(val) + ', '
        my_str = my_str[:-2] + ']'  # Remove trailing comma at end of list
        return my_str
        
    # ------------------------------------------------------------------------
    def tolist(self):
        """
        Convert the FT8Decode object to a list that matches the wsjtxmon format.
        """
        my_list = [wsjtxmon.MSG_DECODE, 
            self.id_str,
            self.new,
            self.time_str,
            self.snr_str,
            self.dt_str,
            str(self.df),
            self.mode_str,
            self.msg_str,
            self.low_conf,
            self.off_air]
        return my_list


###############################################################################
# Main program.
###############################################################################
if __name__ == "__main__":

    # List of decoded messages from WSJT-X.
    my_msg = [
        [2, 'WSJT-X', 1, '004245', '+14', '+0.1', '2060', '~', 'EA1US K0SH -14', 0, 0],
        [2, 'WSJT-X', 1, '004245', '+03', '+0.1', '2394', '~', 'CQ WY0V EN12', 0, 0],
        [2, 'WSJT-X', 1, '004245', '+10', '+0.1', ' 340', '~', 'CQ N4ZXZ EL98', 0, 0],
        [2, 'WSJT-X', 1, '004245', '+06', '+0.4', ' 682', '~', 'VE2AH WI4R -04', 0, 0],
        [2, 'WSJT-X', 1, '004245', '+05', '+0.1', '2932', '~', 'W3DKT EC1A 73', 0, 0],
        [2, 'WSJT-X', 1, '004245', '+22', '+0.3', '2591', '~', 'CQ VE3XET EN58', 0, 0],
        [2, 'WSJT-X', 1, '004245', '+13', '-0.1', '2875', '~', 'LU1VDF N0STL 73', 0, 0],
        [2, 'WSJT-X', 1, '004245', '+03', '-0.1', ' 400', '~', 'KK4RXE AD0ND -13', 0, 0],
        [2, 'WSJT-X', 1, '004245', '+11', '+0.3', ' 740', '~', 'N3DGE KS5Z RR73', 0, 0],
        [2, 'WSJT-X', 1, '004245', '+16', '+0.3', '1595', '~', 'KN4QDE K4JAF R-01', 0, 0],
        [2, 'WSJT-X', 1, '004245', '+07', '-0.5', ' 952', '~', 'K2QJ CO8LY 73', 0, 0],
        [2, 'WSJT-X', 1, '004245', '-02', '+0.1', '1400', '~', 'K8DID EA1IOK IN62', 0, 0],
        [2, 'WSJT-X', 1, '004245', '-02', '+0.1', '1696', '~', 'K8DID KO4IFY EM74', 0, 0],
        [2, 'WSJT-X', 1, '004245', '+03', '+0.1', '1338', '~', 'LU3QBQ NC4CC EL87', 0, 0],
        [2, 'WSJT-X', 1, '004245', '-04', '+0.1', '2449', '~', '9A3ST K4SAX RRR', 0, 0],
        [2, 'WSJT-X', 1, '004245', '+06', '-1.6', '1205', '~', 'KB1HNZ WB0MTD DM59', 0, 0],
        [2, 'WSJT-X', 1, '004245', '+11', '+0.1', ' 448', '~', 'LZ50YE <WA4HFN> 73', 0, 0],
        [2, 'WSJT-X', 1, '004245', '-11', '+0.1', '1488', '~', 'CQ EA7KQP IM77', 0, 0],
        [2, 'WSJT-X', 1, '004245', '-15', '+0.3', '1845', '~', 'KB1HNZ E75AA -17', 0, 0],
        [2, 'WSJT-X', 1, '004245', '-05', '-0.4', '1554', '~', 'KB1HNZ OM8AA KN09', 0, 0],
        [2, 'WSJT-X', 1, '004245', '-03', '+0.1', '1199', '~', 'BG5IQX N5GIT EL09', 0, 0],
        [2, 'WSJT-X', 1, '004245', '-14', '+0.3', '2499', '~', 'KB1HNZ AJ6TE DM12', 0, 0],
        [2, 'WSJT-X', 1, '004245', '-05', '+0.2', '1354', '~', 'CQ W6AER CM87', 0, 0],
        [2, 'WSJT-X', 1, '004245', '-10', '+0.1', '1477', '~', 'VE3WWN S51TA -14', 0, 0],
        [2, 'WSJT-X', 1, '004245', '-10', '+0.1', '2970', '~', 'VE2TK KD5WJV RR73', 0, 0],
        [2, 'WSJT-X', 1, '004245', '-05', '-0.3', '1608', '~', 'WW2FLY AD0TP RRR', 0, 0],
        [2, 'WSJT-X', 1, '004245', '-14', '+0.0', '2235', '~', 'MW6PNW K2RU -16', 0, 0],
        [2, 'WSJT-X', 1, '004245', '-17', '+0.4', '2728', '~', 'RZ4M DC9YH R-10', 0, 0],
        [2, 'WSJT-X', 1, '004245', '+05', '+0.4', ' 449', '~', 'IK4LZH WE9G EM75', 0, 0],
        [2, 'WSJT-X', 1, '004245', '-05', '+0.3', '2575', '~', 'CQ WM8Q DN61', 0, 0],
        [2, 'WSJT-X', 1, '004245', '+01', '+0.2', ' 447', '~', 'IK4LZH W3PT EM73', 0, 0],
        [2, 'WSJT-X', 1, '004245', '-09', '+0.2', '1188', '~', 'CQ CO3HK EL82', 0, 0],
        [2, 'WSJT-X', 1, '004245', '-22', '+0.1', '2508', '~', 'CQ EI9JA IO53', 0, 0],
        [2, 'WSJT-X', 1, '004245', '-16', '+0.1', '1495', '~', 'KB1HNZ W6PJD DM09', 0, 0],
        [2, 'WSJT-X', 1, '004245', '+17', '+1.1', '1289', '~', 'WA8CAC VE4YH R-05', 0, 0],
        [2, 'WSJT-X', 1, '004245', '-17', '+0.2', '1141', '~', 'CQ KJ7VRI DN41', 0, 0],
    ]
    
    # Convert WSJT-X decoded messages to FT8Decode objects.
    my_decode = []
    for msg in my_msg:
        my_decode.append(FT8Decode(msg))
    
    # Example 1: sort by frequency.
    my_decode_sorted = sorted(my_decode, key=attrgetter('df'))
    print('Decoded messages sorted by frequency: ')
    for d in my_decode_sorted:
        print('  ', d)
        
    # Example 2: Print CQ messages reverse sorted by SNR.
    my_decode_sorted = sorted(my_decode, key=attrgetter('snr'), reverse=True)
    print('CQ messages reverse sorted by SNR: ')
    for d in my_decode_sorted:
        if d.msg_str.startswith('CQ '):
            print('  ', d)

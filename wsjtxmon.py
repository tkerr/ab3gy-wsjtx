###############################################################################
# wsjtxmon.py
# Author: Tom Kerr AB3GY
#
# Python class for monitoring WSJT-X messages over a UDP port (Python 3 required).
# Supports WSJT-X Version 2.2.0 and later.
# WSJT-X message formats are described in the following WSJT-X source file:
#     src/wsjtx/Network/NetworkMessage.hpp.
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
from __future__ import print_function

# System level packages.
import getopt
import os
import socket
import sys

# Local packages.
import decode
import encode
from QColor import QColor


##############################################################################
# Global objects and data.
##############################################################################


##############################################################################
# Functions.
##############################################################################


###############################################################################
# Start of wsjtxmon class.
###############################################################################
class wsjtxmon (object):
    """
    WSJT-X message monitoring class.
    Listens on a UDP port as a server and parses WSJT-X messages as they arrive.
    Supports WSJT-X Version 2.2.0 and later.
    WSJT-X message formats are described in the following WSJT-X source file:
        src/wsjtx/Network/NetworkMessage.hpp.
    """
    
    # Static constants and message numbers.
    MAGIC = int(0xADBCCBDA)
    MSG_HEARTBEAT      = int(0)
    MSG_STATUS         = int(1)
    MSG_DECODE         = int(2)
    MSG_CLEAR          = int(3)
    MSG_REPLY          = int(4)
    MSG_QSO_LOGGED     = int(5)
    MSG_CLOSE          = int(6)
    MSG_REPLAY         = int(7)
    MSG_HALT_TX        = int(8)
    MSG_FREE_TEXT      = int(9)
    MSG_WSPR_DECODE    = int(10)
    MSG_LOCATION       = int(11)
    MSG_ADIF_LOGGED    = int(12)
    MSG_HIGHLIGHT_CALL = int(13)
    MSG_SWITCH_CONFIG  = int(14)
    MSG_CONFIGURE      = int(15)
    MSG_SOCKET_ERROR   = int(97) # Not part of WSJT-X spec, added here
    MSG_TIMEOUT        = int(98) # Not part of WSJT-X spec, added here
    MSG_NONE           = int(99) # Not part of WSJT-X spec, added here

    # ------------------------------------------------------------------------
    def __init__(self, verbose=False):
        """
        Class constructor.
        
        Parameters
        ----------
        ip_addr : str
            The local IP address to monitor.  
            WSJT-X must be configured to send packets to this address.
        ip_port : int
            The local port number to monitor.
            WSJT-X must be configured to send packets to this port.
        verbose : bool
            Prints verbose debug messages if True.
        timeout : int
            The socket listen timeout in seconds.
            WSJT-X is expected to send UDP packets at least every 15 seconds.
        
        Returns
        -------
        None
        """
        
        # Variable initialization.
        self.__version__ = str("0.2")  # Version per PEP 396
        self.class_name  = str(type(self).__name__)
        self.IpAddr  = str("")
        self.IpPort  = int(0)
        self.DstAddr = str("")
        self.MsgId   = str("WSJTXMON")  # Message ID (unique key)
        self.Verbose = verbose        
        self.Message = [self.MSG_NONE]
        self.Reply   = bytearray(0)
        self.Schema  = int(0)
        self.Timeout = int(16)
        
        # WSJT-X data is transferred in big-endian format.
        self._endian = 'big'
        
        # Initialize the UDP socket.
        self.Socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # ------------------------------------------------------------------------
    def __del__(self):
        """
        Class destructor.
        Closes the UDP port.
        """ 
        self.Socket.close()


    ###########################################################################
    # Class methods intended to be public.
    ###########################################################################
    
    def bind(self, ip_addr, ip_port, timeout=16):
        """
        Bind the UDP socket to the specified IP address and port.
        
        Parameters
        ----------
        ip_addr : str
            The local IP address to monitor.  
            WSJT-X must be configured to send packets to this address.
        ip_port : int
            The local port number to monitor.
            WSJT-X must be configured to send packets to this port.
        timeout : int
            The socket listen timeout in seconds.
            WSJT-X is expected to send UDP packets at least every 15 seconds.
        
        Returns
        -------
        (status, err_msg) : tuple
            status : bool
                True if bind was successful, False otherwise.
            err_msg : str
                Error message if bind was unsuccessful.
        """
        status = False
        err_msg = ''
        
        # Expecting data at least every 15 seconds.
        # We are the server and listen on our IP address.
        # WSJT-X must be configured to send packets to our address.
        self.IpAddr  = str(ip_addr)
        self.IpPort  = int(ip_port)
        self.Timeout = int(timeout)
        
        # Close existing socket.
        # Ignore errors.
        try:
            self.Socket.close()
        except Exception as err:
            pass
        
        # Initialize the UDP socket and bind to the IP address and port.
        try:
            self.Socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.Socket.settimeout(self.Timeout)
            self.Socket.bind((self.IpAddr, self.IpPort))
            status = True
        except Exception as err:
            err_msg = str(err)
            
        return (status, err_msg)

    # ------------------------------------------------------------------------    
    def get_message(self):
        """
        Get the next message from the UDP port.
        Blocks until message received, socket timeout, or socket error.
        Message is available in the self.Message variable as a list.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        status : bool
            True if successful, False otherwise.
            Returns True on a timeout and False if a socket error occurs.
        """
        ok = False
        self.Message = [self.MSG_NONE]
        try:
            data, self.DstAddr = self.Socket.recvfrom(2048) # buffer size is 2048 bytes
            self._parse_data(data)
            ok = True
        except socket.timeout as err:
            self.Message = [self.MSG_TIMEOUT, str(err)]
            ok = True
            if self.Verbose:
                self._print_error("get_message: " + str(err))
        except Exception as err:
            self.Message = [self.MSG_SOCKET_ERROR, str(err)]
            if self.Verbose:
                self._print_error("get_message: " + str(err))
        return ok

    # ------------------------------------------------------------------------    
    def send_highlight(self, call, *, 
        bg_name=QColor.COLOR_YELLOW, 
        fg_name=QColor.COLOR_BLACK, 
        bg_rgba=None, 
        fg_rgba=None,
        last=True):
        """
        Send a HIGHLIGHT CALLSIGN message to WSJT-X
        
        Parameters
        ----------
        call : str
            The callsign to highlight.
        bg_name : int
            The background color as a pre-defined QColor name (e.g., QColor.COLOR_RED).
            Default is QColor.COLOR_YELLOW.
            Set this to QColor.COLOR_INVALID to clear and disable highlighting.
            Specifying a value for bg_rgba overrides this parameter.
        fg_name : int
            The foreground color as a pre-defined QColor name.
            Default is QColor.COLOR_BLACK.
            Set to QColor.COLOR_BLACK if not specified.
            Specifying a value for fg_rgba overrides this parameter.
        bg_rgba : int
            The background color as a 32-bit RGBA value.  If specified, this
            value overrides the bg_name parameter.
        fg_rgba : int
            The foreground color as a 32-bit RGBA value.  If specified, this
            value overrides the fg_name parameter.
        last : bool
            Highlight callsign in last period only if true, otherwise highlight
            in all periods.

        Returns
        -------
        status : bool
            True if successful, False otherwise
        """
        ok = False
        bgcolor = QColor(name=bg_name)
        fgcolor = QColor(name=fg_name)
        ilast = 0
        if last: ilast = 1
        
        # RGBA values override color names.
        if (bg_rgba is not None):
            bgcolor.setByValue(rgba=bg_rgba)
        if (fg_rgba is not None):
            fgcolor.setByValue(rgba=fg_rgba)
        
        # Create the message buffer.
        data = bytearray(encode.ulong(self.MAGIC, self._endian))    # Magic number
        data.extend(encode.ulong(self.Schema, self._endian))        # Schema
        data.extend(encode.ulong(wsjtxmon.MSG_HIGHLIGHT_CALL, self._endian)) # Message number
        data.extend(encode.ulong(len(self.MsgId), self._endian))    # Message ID (unique key) length
        data.extend(encode.string(self.MsgId))                      # Message ID (unique key) string
        data.extend(encode.ulong(len(call), self._endian))          # Callsign length
        data.extend(encode.string(call))                            # Callsign string
        data.extend(bgcolor.encode())                               # Background color
        data.extend(fgcolor.encode())                               # Foreground color
        data.extend(encode.byte(ilast, self._endian))               # Highlight Last period only flag      
        # Send it.
        try:
            self.Socket.sendto(data, self.DstAddr)
            ok = True
        except Exception as err:
            if self.Verbose:
                self._print_error("send_highlight: " + str(err))
                
        return ok

    # ------------------------------------------------------------------------    
    def send_reply(self, reply=bytearray(0)):
        """
        Send a reply to to WSJT-X.
        The reply message of the last successful decode message is contained 
        in the self.Reply variable as a byte array.
        
        Parameters
        ----------
        reply : bytearray
            The reply message as a byte array.  If not specified, then the
            a reply of the last successful decode message is sent.
        
        Returns
        -------
        status : bool
            True if successful, False otherwise.
        """
        ok = False
        if (len(reply) < 2): reply = self.Reply
        
        try:
            self.Socket.sendto(reply, self.DstAddr)
            ok = True
        except Exception as err:
            if self.Verbose:
                self._print_error("send_reply: " + str(err))
        return ok


    ###########################################################################
    # Class methods intended to be private.
    ###########################################################################
    
    def _make_date_str(self, julian_day):
        """
        Convert Julian Day number to a year, month, day string.
        Algorithm found here: https://quasar.as.utexas.edu/BillInfo/JulianDatesG.html
        
        Parameters
        ----------
        julian_day : int
            The Julian Day to convert.  The Julian Day for the Unix Epoch 
            is 2440588 and should convert to 01-Jan-1970.
        
        Returns
        -------
        date_str : str
            The date string in the format "YYYYMMDD"
        """
        Z = int(julian_day)
        W = int((Z-1867216.25)/36524.25)
        X = int(W/4)
        A = Z+1+W-X
        B = A+1524
        C = int((B-122.1)/365.25)
        D = int(365.25*C)
        E = int((B-D)/30.6001)
        F = int(30.6001*E)
        day = B-D-F
        month = E-1
        if (month > 12): 
            month -= 12
        if (month < 3):
            year = C-4715
        else:
            year = C-4716
        date_str = str("%04d" % year) + str("%02d" % month) + str("%02d" % day)
        return date_str

    # ------------------------------------------------------------------------    
    def _make_time_str(self, elapsed_ms):
        """
        Convert milliseconds since midnight to an hours, minutes, seconds string.
        
        Parameters
        ----------
        elapsed_ms : int
            The elapsed milliseconds since midnight of the current day.
        
        Returns
        -------
        time_str : str
            The time string in the format "HHMMSS"
        """
        elapsed_seconds = int(elapsed_ms / 1000)
        hours = int(elapsed_seconds / 3600)
        remaining_seconds = int(elapsed_seconds - (hours * 3600))
        minutes = int(remaining_seconds / 60)
        seconds = int(remaining_seconds - (minutes * 60))
        time_str = str("%02d" % hours) + str("%02d" % minutes) + str("%02d" % seconds)
        return time_str

    # ------------------------------------------------------------------------    
    def _print_error(self, msg):
        """
        Print an error message to sdterr.
        
        Parameters
        ----------
        msg : str
            The error message to print.
        
        Returns
        -------
        None
        """
        print("\n" + self.class_name + ': ' + msg, file=sys.stderr)    

    # ------------------------------------------------------------------------    
    def _print_hex(self, data):
        """
        Print data as a series of hex bytes.
        
        Parameters
        ----------
        data : bytearray
            The data to format and print.
        
        Returns
        -------
        None
        """
        for d in data:
            sys.stderr.write("%02X " % (d))
        print(" ")

    # ------------------------------------------------------------------------    
    def _parse_utf8(self, data):
        """
        Convert a byte array to a UTF-8 encoded string.
        
        Type utf8 is a utf-8 byte string formatted as a QByteArray for
        serialization purposes (currently a quint32 size followed by size
        bytes, no terminator is present or counted).
        
        Parameters
        ----------
        data : bytearray
            The data array to convert.
        
        Returns
        -------
        (utf8_len, utf8_str) : tuple
            utf8_len : int
                The string length.
            utf8_str : str
                The converted string.
        """
        utf8_len = decode.ulong(data[0:4], self._endian)
        if (utf8_len == 0xFFFFFFFF):  # Null string indicator
            utf8_len = 0
            utf8_str = str("")
        else:
            utf8_str = decode.string(data[4:], utf8_len, 'utf-8')
        return utf8_len, utf8_str
   
    # ------------------------------------------------------------------------    
    def _parse_adif_logged(self, data):
        """
        Parse the WSJT-X ADIF LOGGED message.
        Results of successful parsing are available in the self.Message list.
        
        Parameters
        ----------
        data : bytearray
            The data array containing the message to parse.
        
        Returns
        -------
        None.  The parsed message is available in the self.Message list.
        """
        id_len, id_str = self._parse_utf8(data)  # Message ID string (unique key)
        index = 4 + id_len
        adif_len, adif_str = self._parse_utf8(data[index:])  # ADIF record
        self.Message = [self.MSG_ADIF_LOGGED, id_str, adif_str]

    # ------------------------------------------------------------------------    
    def _parse_clear(self, data):
        """
        Parse the WSJT-X CLEAR message.
        Results of successful parsing are available in the self.Message list.
        
        Parameters
        ----------
        data : bytearray
            The data array containing the message to parse.
        
        Returns
        -------
        None.  The parsed message is available in the self.Message list.
        """
        window = 0
        id_len, id_str = self._parse_utf8(data)    # Message ID string (unique key)
        index = 4 + id_len
        if (index < len(data)):
            window = decode.byte(data[index:index+1]) # Window
            index += 1
        self.Message = [self.MSG_CLEAR, id_str, window]

    # ------------------------------------------------------------------------
    def _parse_close(self, data):
        """
        Parse the WSJT-X CLOSE message.
        Results of successful parsing are available in the self.Message list.
        
        Parameters
        ----------
        data : bytearray
            The data array containing the message to parse.
        
        Returns
        -------
        None.  The parsed message is available in the self.Message list.
        """
        id_len, id_str = self._parse_utf8(data)  # Message ID string (unique key)
        self.Message = [self.MSG_CLOSE, id_str]

    # ------------------------------------------------------------------------    
    def _parse_decode(self, data):
        """
        Parse the WSJT-X DECODE message.
        Results of successful parsing are available in the self.Message list.
        
        Parameters
        ----------
        data : bytearray
            The data array containing the message to parse.
        
        Returns
        -------
        None.  The parsed message is available in the self.Message list.
        """
        
        # Initialize the reply buffer.
        self.Reply = bytearray(encode.ulong(self.MAGIC, self._endian))
        self.Reply.extend(encode.ulong(self.Schema, self._endian))
        self.Reply.extend(encode.ulong(self.MSG_REPLY, self._endian))
        self.Reply.extend(encode.ulong(len(self.MsgId), self._endian))
        self.Reply.extend(encode.string(self.MsgId))
        
        # Parse the DECODE message.
        id_len, id_str = self._parse_utf8(data)                      # Message ID string (unique key)
        index = 4 + id_len
        
        new = decode.byte(data[index:index+1])                       # New flag (0 for replay, 1 otherwise)
        index += 1
        
        elapsed_ms = decode.ulong(data[index:index+4], self._endian) # Milliseconds since midnight
        self.Reply.extend(data[index:index+4])                       # Add to reply message
        index += 4
        
        snr = decode.long(data[index:index+4], self._endian)         # SNR
        self.Reply.extend(data[index:index+4])                       # Add to reply message
        snr_str = str("%+02d" % snr).zfill(3)
        index += 4
        
        delta_time = decode.double(data[index:index+8])              # Delta time in seconds
        self.Reply.extend(data[index:index+8])                       # Add to reply message
        dt_str = str("%+.1f" % delta_time)
        index += 8
        
        freq = decode.ulong(data[index:index+4])                     # Delta frequency
        self.Reply.extend(data[index:index+4])                       # Add to reply message
        df_str = str("%4d" % freq)
        index += 4
        
        mode_len, mode_str = self._parse_utf8(data[index:])          # Mode string
        self.Reply.extend(data[index:index+4])                       # Add length to reply message
        self.Reply.extend(encode.string(mode_str))                   # Add string to reply message
        index += 4 + mode_len
        
        msg_len, msg_str = self._parse_utf8(data[index:])            # Message text
        self.Reply.extend(data[index:index+4])                       # Add length to reply message
        self.Reply.extend(encode.string(msg_str))                    # Add string to reply message
        index += 4 + msg_len
        
        low_conf = decode.byte(data[index:index+1])                  # Low confidence flag
        self.Reply.extend(data[index:index+1])                       # Add to reply message
        index += 1
        
        off_air = decode.byte(data[index:index+1])                   # Off air flag
        index += 1
        
        # Add modifiers to reply message.
        self.Reply.extend(encode.byte(0, self._endian))
    
        # Convert milliseconds since midnight to hours, minutes, seconds.
        time_str = self._make_time_str(elapsed_ms)
    
        self.Message = [self.MSG_DECODE, id_str, new, time_str, snr_str, 
            dt_str, df_str, mode_str, msg_str, low_conf, off_air]

        #self._print_hex(self.Reply)
        #print(self.Reply)

    # ------------------------------------------------------------------------    
    def _parse_heartbeat(self, data):
        """
        Parse the WSJT-X HEARTBEAT message.
        Results of successful parsing are available in the self.Message list.
        
        Parameters
        ----------
        data : bytearray
            The data array containing the message to parse.
        
        Returns
        -------
        None.  The parsed message is available in the self.Message list.
        """
        id_len, id_str = self._parse_utf8(data)  # Message ID string (unique key)
        index = 4 + id_len
        
        max_schema = decode.ulong(data[index:index+4])    # Maximum schema number
        index += 4
        
        ver_len, ver_str = self._parse_utf8(data[index:]) # Version
        index += 4 + ver_len
        
        rev_len, rev_str = self._parse_utf8(data[index:]) # Revision
        self.Message = [self.MSG_HEARTBEAT, id_str, max_schema, ver_str, rev_str]

    # ------------------------------------------------------------------------    
    def _parse_status(self, data): 
        """
        Parse the WSJT-X STATUS message.
        Results of successful parsing are available in the self.Message list.
        
        Parameters
        ----------
        data : bytearray
            The data array containing the message to parse.
        
        Returns
        -------
        None.  The parsed message is available in the self.Message list.
        """
        id_len, id_str = self._parse_utf8(data)  # Message ID string (unique key)
        index = 4 + id_len
        
        freq = decode.uquad(data[index:index+8])                # Dial frequency
        index += 8
        
        mode_len, mode_str = self._parse_utf8(data[index:])     # Mode
        index += 4 + mode_len
        
        dxcall_len, dxcall_str = self._parse_utf8(data[index:]) # DX call
        index += 4 + dxcall_len
        
        report_len, report_str = self._parse_utf8(data[index:]) # Signal report
        index += 4 + report_len
        
        txmode_len, txmode_str = self._parse_utf8(data[index:]) # TX mode
        index += 4 + txmode_len
        
        tx_enable = decode.byte(data[index:index+1])            # TX enable flag
        index += 1
        
        tx_now = decode.byte(data[index:index+1])               # Transmitting flag
        index += 1
        
        decoding = decode.byte(data[index:index+1])             # Decoding flag
        index += 1
        
        rx_df = decode.ulong(data[index:index+4])               # RX delta frequency
        index += 4
        
        tx_df = decode.ulong(data[index:index+4])               # TX delta frequency
        index += 4
        
        decall_len, decall_str = self._parse_utf8(data[index:]) # DE call
        index += 4 + decall_len
        
        degrid_len, degrid_str = self._parse_utf8(data[index:]) # DE grid
        index += 4 + degrid_len
        
        dxgrid_len, dxgrid_str = self._parse_utf8(data[index:]) # DX grid
        index += 4 + dxgrid_len
        
        tx_watchdog = decode.byte(data[index:index+1])          # TX watchdog flag 
        index += 1
        
        submode_len, submode_str = self._parse_utf8(data[index:]) # Sub-mode
        if (submode_len == 0):
            submode_str = "."
        index += 4 + submode_len
        
        fastmode = decode.byte(data[index:index+1])             # Fast mode flag 
        index += 1
        
        specialopmode = decode.byte(data[index:index+1])        # Special operation mode 
        index += 1
        
        freq_tol = decode.ulong(data[index:index+4])            # Frequency tolerance
        index += 4
        
        tr_period = decode.ulong(data[index:index+4])           # T/R period
        index += 4
        
        cfgname_len, cfgname_str = self._parse_utf8(data[index:]) # Configuration name
        index += 4 + cfgname_len
        
        self.Message = [self.MSG_STATUS, id_str, freq, mode_str, dxcall_str, 
            report_str, txmode_str, tx_enable, tx_now, decoding, tx_df, rx_df, 
            decall_str, degrid_str, dxgrid_str, tx_watchdog, submode_str, 
            fastmode, specialopmode, freq_tol, tr_period, cfgname_str]

    # ------------------------------------------------------------------------        
    def _parse_qso_logged(self, data):
        """
        Parse the WSJT-X QSO LOGGED message.
        Results of successful parsing are available in the self.Message list.
        
        Parameters
        ----------
        data : bytearray
            The data array containing the message to parse.
        
        Returns
        -------
        None.  The parsed message is available in the self.Message list.
        """
        id_len, id_str = self._parse_utf8(data)  # Message ID string (unique key)
        index = 4 + id_len
        
        ### Time Off ###
        tz_offset = 0
        date_off = decode.uquad(data[index:index+8])     # QDate = Julian Day Number
        index += 8
        time_off = decode.ulong(data[index:index+4])     # Milliseconds since midnight
        index += 4
        timespec = decode.byte(data[index:index+1])      # QDateTime timespec 
        index += 1
        if (timespec == 2):
            tz_offset = decode.long(data[index:index+4]) # Timezone offset
            index += 4
        date_off_str = self._make_date_str(date_off)
        time_off_str = self._make_time_str(time_off)
            
        dxcall_len, dxcall_str = self._parse_utf8(data[index:])  # DX call
        index += 4 + dxcall_len
        
        dxgrid_len, dxgrid_str = self._parse_utf8(data[index:])  # DX grid
        index += 4 + dxgrid_len
        
        freq = decode.uquad(data[index:index+8])                 # Dial frequency
        index += 8
        
        mode_len, mode_str = self._parse_utf8(data[index:])      # Mode
        index += 4 + mode_len
        
        report_sent_len, report_sent_str = self._parse_utf8(data[index:])  # Report sent
        index += 4 + report_sent_len
        
        report_recd_len, report_recd_str = self._parse_utf8(data[index:])  # Report received
        index += 4 + report_recd_len
        
        power_len, power_str = self._parse_utf8(data[index:])              # TX power
        index += 4 + power_len
        
        comments_len, comments_str = self._parse_utf8(data[index:])        # Comments
        index += 4 + comments_len
        
        name_len, name_str = self._parse_utf8(data[index:])                # Name
        index += 4 + name_len
        
        ### Time On ###
        date_on = decode.uquad(data[index:index+8])       # QDate
        index += 8
        time_on = decode.ulong(data[index:index+4])       # Milliseconds since midnight
        index += 4
        timespec = decode.byte(data[index:index+1])       # QDateTime timespec 
        index += 1
        if (timespec == 2):
            tz_offset = decode.long(data[index:index+4])  # Timezone offset
            index += 4
        date_on_str = self._make_date_str(date_on)
        time_on_str = self._make_time_str(time_on)

        opcall_len, opcall_str = self._parse_utf8(data[index:])        # Operator call
        index += 4 + opcall_len
        
        mycall_len, mycall_str = self._parse_utf8(data[index:])        # My call
        index += 4 + mycall_len
        
        mygrid_len, mygrid_str = self._parse_utf8(data[index:])        # My grid
        index += 4 + mygrid_len
        
        exch_sent_len, exch_sent_str = self._parse_utf8(data[index:])  # Exchange sent
        index += 4 + exch_sent_len
        
        exch_rcvd_len, exch_rcvd_str = self._parse_utf8(data[index:])  # Exchange received
        index += 4 + exch_rcvd_len
            
        self.Message = [self.MSG_QSO_LOGGED, id_str, date_off_str, time_off_str, 
            dxcall_str, dxgrid_str, freq, mode_str, report_sent_str, report_recd_str, 
            power_str, comments_str, name_str, date_on_str, time_on_str, opcall_str,
            mycall_str, mygrid_str, exch_sent_str, exch_rcvd_str]

    # ------------------------------------------------------------------------        
    def _parse_wspr_decode(self, data):
        """
        Parse the WSJT-X WSPR DECODE message.
        Results of successful parsing are available in the self.Message list.
        
        Parameters
        ----------
        data : bytearray
            The data array containing the message to parse.
        
        Returns
        -------
        None.  The parsed message is available in the self.Message list.
        """
        id_len, id_str = self._parse_utf8(data)  # Message ID string (unique key)
        index = 4 + id_len
        
        new = decode.byte(data[index:index+1])                  # New flag (0 for replay, 1 otherwise)
        index += 1    
        
        elapsed_ms = decode.ulong(data[index:index+4])          # Milliseconds since midnight
        index += 4   
        
        snr = decode.long(data[index:index+4])                  # SNR
        snr_str = str("%+02d" % snr).zfill(3)
        index += 4
        
        delta_time = decode.double(data[index:index+8])         # Delta time in seconds
        dt_str = str("%+.1f" % delta_time)
        index += 8       
        
        freq = decode.uquad(data[index:index+8])                # Frequency
        freq_str = str("%6d" % freq)
        index += 8
        
        drift = decode.long(data[index:index+4])                # Drift
        index += 4
        
        dxcall_len, dxcall_str = self._parse_utf8(data[index:]) # DX call
        index += 4 + dxcall_len
        
        dxgrid_len, dxgrid_str = self._parse_utf8(data[index:]) # DX grid
        index += 4 + dxgrid_len
        
        dbm = decode.long(data[index:index+4])                  # Power in dBm
        dbm_str = str(dbm)
        index += 4
        
        off_air = decode.byte(data[index:index+1])              # Off air flag
        index += 1
        
        # Convert milliseconds since midnight to hours, minutes, seconds.
        time_str = self._make_time_str(elapsed_ms)
        
        self.Message = [self.MSG_WSPR_DECODE, id_str, new, time_str, snr_str, dt_str, 
            freq_str, dxcall_str, dxgrid_str, dbm_str, off_air]

    # ------------------------------------------------------------------------    
    def _parse_data(self, data):
        """
        Parse the data buffer received from the UDP port.
        Results of successful parsing are available in the self.Message list.
        
        Parameters
        ----------
        data : bytearray
            The data array containing the message to parse.
        
        Returns
        -------
        None.  The parsed message is available in the self.Message list.
        """
        self.Message = [self.MSG_NONE]
        magic_num    = decode.ulong(data[0:4],  self._endian)
        self.Schema  = decode.ulong(data[4:8],  self._endian)  # Schema number
        msg_num      = decode.ulong(data[8:12], self._endian)  # Message number
        
        if (magic_num == self.MAGIC):
            if (msg_num == self.MSG_HEARTBEAT):
                self._parse_heartbeat(data[12:])
            elif (msg_num == self.MSG_STATUS):
                self._parse_status(data[12:])
            elif (msg_num == self.MSG_DECODE):
                self._parse_decode(data[12:])
            elif (msg_num == self.MSG_CLEAR):
                self._parse_clear(data[12:])
            elif (msg_num == self.MSG_QSO_LOGGED):
                self._parse_qso_logged(data[12:])
            elif (msg_num == self.MSG_CLOSE):
                self._parse_close(data[12:])
            elif (msg_num == self.MSG_WSPR_DECODE):
                self._parse_wspr_decode(data[12:])
            elif (msg_num == self.MSG_ADIF_LOGGED):
                self._parse_adif_logged(data[12:])
            else:
                self.Message = [msg_num]
                if self.Verbose:
                    self._print_error("Unsupported message number: " + str(msg_num))
                    self._print_hex(data)
        elif self.Verbose:
            self._print_error("Invalid message header")

###############################################################################
# End of wsjtxmon class.
###############################################################################
   

###############################################################################
# Main program.
# Monitor the UDP port and print messages.
###############################################################################

if __name__ == "__main__":

    udp_ip   = "127.0.0.1"
    udp_port = 2237
    timeout  = 16
    verbose  = False

    # Get command line options and arguments.
    try:
        (opts, args) = getopt.getopt(sys.argv[1:], "a:p:t:v")
    except (getopt.GetoptError) as err:
        print_error(str(err))
        print_usage()

    for (o, a) in opts:
        if (o == "-a"):
            udp_ip = a
        if (o == "-p"):
            udp_port = int(a, 10)
        if (o == "-t"):
            timeout = int(a, 10)
            
        if (o == "-v"):
            verbose = True

    monitor = wsjtxmon(verbose)
    (status, err_msg) = monitor.bind(udp_ip, udp_port, timeout)
    if not status:
        print('wsjtxmon bind error: ' + err_msg)
        sys.exit(1)

    # Loop forever until socket error or WSJT-X application close.
    # Can also use CTRL-C to interrupt and exit.
    ok = True
    while ok:
        ok = monitor.get_message()
        print(monitor.Message)
        if (monitor.Message[0] == monitor.MSG_CLOSE):
            ok = False

# End of file.
    
# MIT License
#
# Copyright (c) 2016-2023 Mark Qvist / unsigned.io
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from .Interface import Interface
from time import sleep
import sys
import threading
import time
import math
import RNS

class KISS():
    FEND            = 0xC0
    FESC            = 0xDB
    TFEND           = 0xDC
    TFESC           = 0xDD
    
    CMD_UNKNOWN     = 0xFE
    CMD_DATA        = 0x00
    CMD_FREQUENCY   = 0x01
    CMD_BANDWIDTH   = 0x02
    CMD_TXPOWER     = 0x03
    CMD_SF          = 0x04
    CMD_CR          = 0x05
    CMD_RADIO_STATE = 0x06
    CMD_RADIO_LOCK  = 0x07
    CMD_ST_ALOCK    = 0x0B
    CMD_LT_ALOCK    = 0x0C
    CMD_DETECT      = 0x08
    CMD_LEAVE       = 0x0A
    CMD_READY       = 0x0F
    CMD_STAT_RX     = 0x21
    CMD_STAT_TX     = 0x22
    CMD_STAT_RSSI   = 0x23
    CMD_STAT_SNR    = 0x24
    CMD_STAT_CHTM   = 0x25
    CMD_STAT_PHYPRM = 0x26
    CMD_BLINK       = 0x30
    CMD_RANDOM      = 0x40
    CMD_FB_EXT      = 0x41
    CMD_FB_READ     = 0x42
    CMD_FB_WRITE    = 0x43
    CMD_BT_CTRL     = 0x46
    CMD_PLATFORM    = 0x48
    CMD_MCU         = 0x49
    CMD_FW_VERSION  = 0x50
    CMD_ROM_READ    = 0x51
    CMD_RESET       = 0x55
    CMD_INTERFACES  = 0x64

    CMD_INT0_DATA   = 0x00
    CMD_INT1_DATA   = 0x10
    CMD_INT2_DATA   = 0x20
    CMD_INT3_DATA   = 0x70
    CMD_INT4_DATA   = 0x80
    CMD_INT5_DATA   = 0x90
    CMD_INT6_DATA   = 0xA0
    CMD_INT7_DATA   = 0xB0
    CMD_INT8_DATA   = 0xC0
    CMD_INT9_DATA   = 0xD0
    CMD_INT10_DATA  = 0xE0
    CMD_INT11_DATA  = 0xF0

    CMD_SEL_INT0    = 0x1E
    CMD_SEL_INT1    = 0x1F
    CMD_SEL_INT2    = 0x2F
    CMD_SEL_INT3    = 0x7F
    CMD_SEL_INT4    = 0x8F
    CMD_SEL_INT5    = 0x9F
    CMD_SEL_INT6    = 0xAF
    CMD_SEL_INT7    = 0xBF
    CMD_SEL_INT8    = 0xCF
    CMD_SEL_INT9    = 0xDF
    CMD_SEL_INT10   = 0xEF
    CMD_SEL_INT11   = 0xFF

    DETECT_REQ      = 0x73
    DETECT_RESP     = 0x46
    
    RADIO_STATE_OFF = 0x00
    RADIO_STATE_ON  = 0x01
    RADIO_STATE_ASK = 0xFF
    
    CMD_ERROR           = 0x90
    ERROR_INITRADIO     = 0x01
    ERROR_TXFAILED      = 0x02
    ERROR_EEPROM_LOCKED = 0x03

    PLATFORM_AVR   = 0x90
    PLATFORM_ESP32 = 0x80

    SX1276    = 0x01
    SX1278    = 0x02
    SX1262    = 0x03
    SX1280    = 0x04

    def index_to_selector(index):
        match index:
            case 0:
                return KISS.CMD_SEL_INT0
            case 1:
                return KISS.CMD_SEL_INT1
            case 2:
                return KISS.CMD_SEL_INT2
            case 3:
                return KISS.CMD_SEL_INT3
            case 4:
                return KISS.CMD_SEL_INT4
            case 5:
                return KISS.CMD_SEL_INT5
            case 6:
                return KISS.CMD_SEL_INT6
            case 7:
                return KISS.CMD_SEL_INT7
            case 8:
                return KISS.CMD_SEL_INT8
            case 9:
                return KISS.CMD_SEL_INT9
            case 10:
                return KISS.CMD_SEL_INT10
            case 11:
                return KISS.CMD_SEL_INT11
            case _:
                return KISS.CMD_SEL_INT0

    def int_data_cmd_to_index(int_data_cmd):
        match int_data_cmd:
            case KISS.CMD_INT0_DATA:
                return 0
            case KISS.CMD_INT1_DATA:
                return 1
            case KISS.CMD_INT2_DATA:
                return 2
            case KISS.CMD_INT3_DATA:
                return 3
            case KISS.CMD_INT4_DATA:
                return 4
            case KISS.CMD_INT5_DATA:
                return 5
            case KISS.CMD_INT6_DATA:
                return 6
            case KISS.CMD_INT7_DATA:
                return 7
            case KISS.CMD_INT8_DATA:
                return 8
            case KISS.CMD_INT9_DATA:
                return 9
            case KISS.CMD_INT10_DATA:
                return 10
            case KISS.CMD_INT11_DATA:
                return 11

    def interface_type_to_str(interface_type):
        match interface_type:
            case KISS.SX1262:
                return "SX1262"
            case KISS.SX1276:
                return "SX1276"
            case KISS.SX1278:
                return "SX1278"
            case KISS.SX1280:
                return "SX1280"

    @staticmethod
    def escape(data):
        data = data.replace(bytes([0xdb]), bytes([0xdb, 0xdd]))
        data = data.replace(bytes([0xc0]), bytes([0xdb, 0xdc]))
        return data
    

class RNodeMultiInterface(Interface):
    MAX_CHUNK = 32768

    RSSI_OFFSET = 157

    CALLSIGN_MAX_LEN    = 32

    REQUIRED_FW_VER_MAJ = 1
    REQUIRED_FW_VER_MIN = 52

    RECONNECT_WAIT = 5

    MAX_SUBINTERFACES = 11

    def __init__(self, owner, name, port, subint_config, id_interval = None, id_callsign = None):
        if RNS.vendor.platformutils.is_android():
            raise SystemError("Invalid interface type. The Android-specific RNode interface must be used on Android")

        import importlib
        if importlib.util.find_spec('serial') != None:
            import serial
        else:
            RNS.log("Using the RNode interface requires a serial communication module to be installed.", RNS.LOG_CRITICAL)
            RNS.log("You can install one with the command: python3 -m pip install pyserial", RNS.LOG_CRITICAL)
            RNS.panic()

        super().__init__()

        self.HW_MTU = 508
        
        self.clients = 0
        self.pyserial    = serial
        self.serial      = None
        self.last_write_index = 0
        self.owner       = owner
        self.name        = name
        self.port        = port
        self.speed       = 115200
        self.databits    = 8
        self.stopbits    = 1
        self.timeout     = 100
        self.online      = False
        self.detached    = False
        self.reconnecting= False

        self.bitrate     = 0
        self.platform    = None
        self.display     = None
        self.mcu         = None
        self.detected    = False
        self.firmware_ok = False
        self.maj_version = 0
        self.min_version = 0
        self.mode        = RNS.Interfaces.Interface.Interface.MODE_FULL

        self.last_id     = 0
        self.first_tx    = None
        self.reconnect_w = RNodeMultiInterface.RECONNECT_WAIT

        self.subinterfaces = [0] * RNodeMultiInterface.MAX_SUBINTERFACES
        self.subinterface_indexes = []
        self.subinterface_types = []
        self.subint_config = subint_config

        self.r_stat_rx   = None
        self.r_stat_tx   = None
        self.r_stat_rssi = None
        self.r_stat_snr  = None
        self.r_st_alock  = None
        self.r_lt_alock  = None
        self.r_random    = None
        self.r_airtime_short      = 0.0
        self.r_airtime_long       = 0.0
        self.r_channel_load_short = 0.0
        self.r_channel_load_long  = 0.0
        self.r_symbol_time_ms = None
        self.r_symbol_rate = None
        self.r_preamble_symbols = None
        self.r_premable_time_ms = None

        self.packet_queue    = []
        self.interface_ready = False
        self.announce_rate_target = None

        self.validcfg  = True
        if id_interval != None and id_callsign != None:
            if (len(id_callsign.encode("utf-8")) <= RNodeMultiInterface.CALLSIGN_MAX_LEN):
                self.should_id = True
                self.id_callsign = id_callsign.encode("utf-8")
                self.id_interval = id_interval
            else:
                RNS.log("The encoded ID callsign for "+str(self)+" exceeds the max length of "+str(RNodeMultiInterface.CALLSIGN_MAX_LEN)+" bytes.", RNS.LOG_ERROR)
                self.validcfg = False
        else:
            self.id_interval = None
            self.id_callsign = None

        if (not self.validcfg):
            raise ValueError("The configuration for "+str(self)+" contains errors, interface is offline")

        try:
            self.open_port()

            if self.serial.is_open:
                self.configure_device()
            else:
                raise IOError("Could not open serial port")

        except Exception as e:
            RNS.log("Could not open serial port for interface "+str(self), RNS.LOG_ERROR)
            RNS.log("The contained exception was: "+str(e), RNS.LOG_ERROR)
            RNS.log("Reticulum will attempt to bring up this interface periodically", RNS.LOG_ERROR)
            if not self.detached and not self.reconnecting:
                thread = threading.Thread(target=self.reconnect_port)
                thread.daemon = True
                thread.start()

    def open_port(self):
        RNS.log("Opening serial port "+self.port+"...")
        self.serial = self.pyserial.Serial(
            port = self.port,
            baudrate = self.speed,
            bytesize = self.databits,
            parity = self.pyserial.PARITY_NONE,
            stopbits = self.stopbits,
            xonxoff = False,
            rtscts = False,
            timeout = 0,
            inter_byte_timeout = None,
            write_timeout = None,
            dsrdtr = False,
        )


    def configure_device(self):
        sleep(2.0)

        thread = threading.Thread(target=self.readLoop)
        thread.daemon = True
        thread.start()

        self.detect()
        sleep(0.2)
        
        if not self.detected:
            RNS.log("Could not detect device for "+str(self), RNS.LOG_ERROR)
            self.serial.close()
        else:
            if self.platform == KISS.PLATFORM_ESP32:
                self.display = True

        RNS.log("Serial port "+self.port+" is now open")
        RNS.log("Creating subinterfaces...", RNS.LOG_VERBOSE)
        index = None
        for subint in self.subint_config:
            for subint_type in self.subinterface_types:
                if subint[0] == subint_type:
                    index = self.subinterface_types.index(subint_type)
            
            # The interface type configured is not present on the RNode
            if index is None:
                raise ValueError("Interface type \""+subint[0]+"\" is not available on "+self.name)

            # interface will add itself to the subinterfaces list automatically
            interface = RNodeSubInterface(
                    RNS.Transport,
                    self,
                    index,
                    subint[0],
                    frequency = subint[1],
                    bandwidth = subint[2],
                    txpower = subint[3],
                    sf = subint[4],
                    cr = subint[5],
                    flow_control=subint[6],
                    st_alock=subint[7],
                    lt_alock=subint[8]
            )

            interface.OUT = True
            interface.IN  = self.IN
            interface.bitrate = self.bitrate
            
            interface.announce_rate_target = self.announce_rate_target
            #interface.announce_rate_grace = self.announce_rate_grace
            #interface.announce_rate_penalty = self.announce_rate_penalty
            interface.mode = self.mode
            interface.HW_MTU = self.HW_MTU
            interface.detected = True
            RNS.Transport.interfaces.append(interface)
            RNS.log("Spawned new RNode subinterface: "+str(interface), RNS.LOG_VERBOSE)

            self.clients += 1

        self.online = True

    def detect(self):
        kiss_command = bytes([KISS.FEND, KISS.CMD_DETECT, KISS.DETECT_REQ, KISS.FEND, KISS.CMD_FW_VERSION, 0x00, KISS.FEND, KISS.CMD_PLATFORM, 0x00, KISS.FEND, KISS.CMD_MCU, 0x00, KISS.FEND, KISS.CMD_INTERFACES, 0x00, KISS.FEND])
        written = self.serial.write(kiss_command)
        if written != len(kiss_command):
            raise IOError("An IO error occurred while detecting hardware for "+str(self))
    
    def leave(self):
        kiss_command = bytes([KISS.FEND, KISS.CMD_LEAVE, 0xFF, KISS.FEND])
        written = self.serial.write(kiss_command)
        if written != len(kiss_command):
            raise IOError("An IO error occurred while sending host left command to device")
    
    def enable_external_framebuffer(self):
        if self.display != None:
            kiss_command = bytes([KISS.FEND, KISS.CMD_FB_EXT, 0x01, KISS.FEND])
            written = self.serial.write(kiss_command)
            if written != len(kiss_command):
                raise IOError("An IO error occurred while enabling external framebuffer on device")

    def disable_external_framebuffer(self):
        if self.display != None:
            kiss_command = bytes([KISS.FEND, KISS.CMD_FB_EXT, 0x00, KISS.FEND])
            written = self.serial.write(kiss_command)
            if written != len(kiss_command):
                raise IOError("An IO error occurred while disabling external framebuffer on device")

    FB_PIXEL_WIDTH     = 64
    FB_BITS_PER_PIXEL  = 1
    FB_PIXELS_PER_BYTE = 8//FB_BITS_PER_PIXEL
    FB_BYTES_PER_LINE  = FB_PIXEL_WIDTH//FB_PIXELS_PER_BYTE
    def display_image(self, imagedata):
        if self.display != None:
            lines = len(imagedata)//8
            for line in range(lines):
                line_start = line*RNodeMultiInterface.FB_BYTES_PER_LINE
                line_end   = line_start+RNodeMultiInterface.FB_BYTES_PER_LINE
                line_data = bytes(imagedata[line_start:line_end])
                self.write_framebuffer(line, line_data)

    def write_framebuffer(self, line, line_data):
        if self.display != None:
            line_byte = line.to_bytes(1, byteorder="big", signed=False)
            data = line_byte+line_data
            escaped_data = KISS.escape(data)
            kiss_command = bytes([KISS.FEND])+bytes([KISS.CMD_FB_WRITE])+escaped_data+bytes([KISS.FEND])
            
            written = self.serial.write(kiss_command)
            if written != len(kiss_command):
                raise IOError("An IO error occurred while writing framebuffer data device")

    def hard_reset(self):
        kiss_command = bytes([KISS.FEND, KISS.CMD_RESET, 0xf8, KISS.FEND])
        written = self.serial.write(kiss_command)
        if written != len(kiss_command):
            raise IOError("An IO error occurred while restarting device")
        sleep(2.25);

    # todo, change to use sel_cmd variable instead of translating to index by function
    def setFrequency(self, frequency, index):
        c1 = frequency >> 24
        c2 = frequency >> 16 & 0xFF
        c3 = frequency >> 8 & 0xFF
        c4 = frequency & 0xFF
        data = KISS.escape(bytes([c1])+bytes([c2])+bytes([c3])+bytes([c4]))

        kiss_command = bytes([KISS.FEND])+bytes([KISS.index_to_selector(index)])+bytes([KISS.FEND])+bytes([KISS.FEND])+bytes([KISS.CMD_FREQUENCY])+data+bytes([KISS.FEND])
        written = self.serial.write(kiss_command)
        if written != len(kiss_command):
            raise IOError("An IO error occurred while configuring frequency for "+str(self))
        self.last_write_index = index

    def setBandwidth(self, bandwidth, index):
        c1 = bandwidth >> 24
        c2 = bandwidth >> 16 & 0xFF
        c3 = bandwidth >> 8 & 0xFF
        c4 = bandwidth & 0xFF
        data = KISS.escape(bytes([c1])+bytes([c2])+bytes([c3])+bytes([c4]))

        kiss_command = bytes([KISS.FEND])+bytes([KISS.index_to_selector(index)])+bytes([KISS.FEND])+bytes([KISS.FEND])+bytes([KISS.CMD_BANDWIDTH])+data+bytes([KISS.FEND])
        written = self.serial.write(kiss_command)
        if written != len(kiss_command):
            raise IOError("An IO error occurred while configuring bandwidth for "+str(self))
        self.last_write_index = index

    def setTXPower(self, txpower, index):
        txp = bytes([txpower])
        kiss_command = bytes([KISS.FEND])+bytes([KISS.index_to_selector(index)])+bytes([KISS.FEND])+bytes([KISS.FEND])+bytes([KISS.CMD_TXPOWER])+txp+bytes([KISS.FEND])
        written = self.serial.write(kiss_command)
        if written != len(kiss_command):
            raise IOError("An IO error occurred while configuring TX power for "+str(self))
        self.last_write_index = index

    def setSpreadingFactor(self, sf, index):
        sf = bytes([sf])
        kiss_command = bytes([KISS.FEND])+bytes([KISS.index_to_selector(index)])+bytes([KISS.FEND])+bytes([KISS.FEND])+bytes([KISS.CMD_SF])+sf+bytes([KISS.FEND])
        written = self.serial.write(kiss_command)
        if written != len(kiss_command):
            raise IOError("An IO error occurred while configuring spreading factor for "+str(self))
        self.last_write_index = index

    def setCodingRate(self, cr, index):
        cr = bytes([cr])
        kiss_command = bytes([KISS.FEND])+bytes([KISS.index_to_selector(index)])+bytes([KISS.FEND])+bytes([KISS.FEND])+bytes([KISS.CMD_CR])+cr+bytes([KISS.FEND])
        written = self.serial.write(kiss_command)
        if written != len(kiss_command):
            raise IOError("An IO error occurred while configuring coding rate for "+str(self))
        self.last_write_index = index

    def setSTALock(self, st_alock, index):
        if st_alock != None:
            at = int(st_alock*100)
            c1 = at >> 8 & 0xFF
            c2 = at & 0xFF
            data = KISS.escape(bytes([c1])+bytes([c2]))

            kiss_command = bytes([KISS.FEND])+bytes([KISS.index_to_selector(index)])+bytes([KISS.FEND])+bytes([KISS.FEND])+bytes([KISS.CMD_ST_ALOCK])+data+bytes([KISS.FEND])
            written = self.serial.write(kiss_command)
            if written != len(kiss_command):
                raise IOError("An IO error occurred while configuring short-term airtime limit for "+str(self))
            self.last_write_index = index

    def setLTALock(self, lt_alock, index):
        if lt_alock != None:
            at = int(lt_alock*100)
            c1 = at >> 8 & 0xFF
            c2 = at & 0xFF
            data = KISS.escape(bytes([c1])+bytes([c2]))

            kiss_command = bytes([KISS.FEND])+bytes([KISS.index_to_selector(index)])+bytes([KISS.FEND])+bytes([KISS.FEND])+bytes([KISS.CMD_LT_ALOCK])+data+bytes([KISS.FEND])
            written = self.serial.write(kiss_command)
            if written != len(kiss_command):
                raise IOError("An IO error occurred while configuring long-term airtime limit for "+str(self))
            self.last_write_index = index

    def setRadioState(self, state, index):
        #self.state = state
        kiss_command = bytes([KISS.FEND])+bytes([KISS.index_to_selector(index)])+bytes([KISS.FEND])+bytes([KISS.FEND])+bytes([KISS.CMD_RADIO_STATE])+bytes([state])+bytes([KISS.FEND])
        written = self.serial.write(kiss_command)
        if written != len(kiss_command):
            raise IOError("An IO error occurred while configuring radio state for "+str(self))
        self.last_write_index = index

    def validate_firmware(self):
        if (self.maj_version >= RNodeMultiInterface.REQUIRED_FW_VER_MAJ):
            if (self.min_version >= RNodeMultiInterface.REQUIRED_FW_VER_MIN):
                self.firmware_ok = True
        
        if self.firmware_ok:
            return

        RNS.log("The firmware version of the connected RNode is "+str(self.maj_version)+"."+str(self.min_version), RNS.LOG_ERROR)
        RNS.log("This version of Reticulum requires at least version "+str(RNodeMultiInterface.REQUIRED_FW_VER_MAJ)+"."+str(RNodeMultiInterface.REQUIRED_FW_VER_MIN), RNS.LOG_ERROR)
        RNS.log("Please update your RNode firmware with rnodeconf from https://github.com/markqvist/rnodeconfigutil/")
        RNS.panic()

    def processOutgoing(self, data, sel_cmd = None):
        if sel_cmd is None:
            # do nothing if RNS tries to transmit on this interface directly
            RNS.log("Attempted transmit!", RNS.LOG_DEBUG)
            pass
        else:
            data    = KISS.escape(data)
            frame   = bytes([0xc0])+bytes([sel_cmd])+data+bytes([0xc0])

            written = self.serial.write(frame)
            self.txb += len(data)

            if written != len(frame):
                raise IOError("Serial interface only wrote "+str(written)+" bytes of "+str(len(data)))

    def received_announce(self, from_spawned=False):
        if from_spawned: self.ia_freq_deque.append(time.time())

    def sent_announce(self, from_spawned=False):
        if from_spawned: self.oa_freq_deque.append(time.time())

    def readLoop(self):
        try:
            in_frame = False
            escape = False
            command = KISS.CMD_UNKNOWN
            data_buffer = b""
            command_buffer = b""
            last_read_ms = int(time.time()*1000)

            while self.serial.is_open:
                if self.serial.in_waiting:
                    byte = ord(self.serial.read(1))
                    last_read_ms = int(time.time()*1000)

                    if (in_frame and byte == KISS.FEND and
                        command == KISS.CMD_INT0_DATA or
                        command == KISS.CMD_INT1_DATA or
                        command == KISS.CMD_INT2_DATA or
                        command == KISS.CMD_INT3_DATA or
                        command == KISS.CMD_INT4_DATA or
                        command == KISS.CMD_INT5_DATA or
                        command == KISS.CMD_INT6_DATA or
                        command == KISS.CMD_INT7_DATA or
                        command == KISS.CMD_INT8_DATA or
                        command == KISS.CMD_INT9_DATA or
                        command == KISS.CMD_INT10_DATA or
                        command == KISS.CMD_INT11_DATA
                        ):
                        in_frame = False
                        self.subinterfaces[KISS.int_data_cmd_to_index(command)].processIncoming(data_buffer)
                        data_buffer = b""
                        command_buffer = b""
                    elif (byte == KISS.FEND):
                        in_frame = True
                        command = KISS.CMD_UNKNOWN
                        data_buffer = b""
                        command_buffer = b""
                    elif (in_frame and len(data_buffer) < self.HW_MTU):
                        if (len(data_buffer) == 0 and command == KISS.CMD_UNKNOWN):
                            command = byte
                        elif (command == KISS.CMD_DATA):
                            if (byte == KISS.FESC):
                                escape = True
                            else:
                                if (escape):
                                    if (byte == KISS.TFEND):
                                        byte = KISS.FEND
                                    if (byte == KISS.TFESC):
                                        byte = KISS.FESC
                                    escape = False
                                data_buffer = data_buffer+bytes([byte])
                        elif (command == KISS.CMD_FREQUENCY):
                            if (byte == KISS.FESC):
                                escape = True
                            else:
                                if (escape):
                                    if (byte == KISS.TFEND):
                                        byte = KISS.FEND
                                    if (byte == KISS.TFESC):
                                        byte = KISS.FESC
                                    escape = False
                                command_buffer = command_buffer+bytes([byte])
                                if (len(command_buffer) == 4):
                                    self.subinterfaces[self.last_write_index].r_frequency = command_buffer[0] << 24 | command_buffer[1] << 16 | command_buffer[2] << 8 | command_buffer[3]
                                    RNS.log(str(self)+" Radio reporting frequency is "+str(self.subinterfaces[self.last_write_index].r_frequency/1000000.0)+" MHz", RNS.LOG_DEBUG)
                                    self.subinterfaces[self.last_write_index].updateBitrate()

                        elif (command == KISS.CMD_BANDWIDTH):
                            if (byte == KISS.FESC):
                                escape = True
                            else:
                                if (escape):
                                    if (byte == KISS.TFEND):
                                        byte = KISS.FEND
                                    if (byte == KISS.TFESC):
                                        byte = KISS.FESC
                                    escape = False
                                command_buffer = command_buffer+bytes([byte])
                                if (len(command_buffer) == 4):
                                    self.subinterfaces[self.last_write_index].r_bandwidth = command_buffer[0] << 24 | command_buffer[1] << 16 | command_buffer[2] << 8 | command_buffer[3]
                                    RNS.log(str(self)+" Radio reporting bandwidth is "+str(self.subinterfaces[self.last_write_index].r_bandwidth/1000.0)+" KHz", RNS.LOG_DEBUG)
                                    self.subinterfaces[self.last_write_index].updateBitrate()

                        elif (command == KISS.CMD_TXPOWER):
                            self.subinterfaces[self.last_write_index].r_txpower = byte
                            RNS.log(str(self)+" Radio reporting TX power is "+str(self.subinterfaces[self.last_write_index].r_txpower)+" dBm", RNS.LOG_DEBUG)
                        elif (command == KISS.CMD_SF):
                            self.subinterfaces[self.last_write_index].r_sf = byte
                            RNS.log(str(self)+" Radio reporting spreading factor is "+str(self.subinterfaces[self.last_write_index].r_sf), RNS.LOG_DEBUG)
                            self.subinterfaces[self.last_write_index].updateBitrate()
                        elif (command == KISS.CMD_CR):
                            self.subinterfaces[self.last_write_index].r_cr = byte
                            RNS.log(str(self)+" Radio reporting coding rate is "+str(self.subinterfaces[self.last_write_index].r_cr), RNS.LOG_DEBUG)
                            self.subinterfaces[self.last_write_index].updateBitrate()
                        elif (command == KISS.CMD_RADIO_STATE):
                            self.subinterfaces[self.last_write_index].r_state = byte
                            if self.subinterfaces[self.last_write_index].r_state:
                                pass
                                #RNS.log(str(self)+" Radio reporting state is online", RNS.LOG_DEBUG)
                            else:
                                RNS.log(str(self)+" Radio reporting state is offline", RNS.LOG_DEBUG)

                        elif (command == KISS.CMD_RADIO_LOCK):
                            self.subinterfaces[self.last_write_index].r_lock = byte
                        elif (command == KISS.CMD_FW_VERSION):
                            if (byte == KISS.FESC):
                                escape = True
                            else:
                                if (escape):
                                    if (byte == KISS.TFEND):
                                        byte = KISS.FEND
                                    if (byte == KISS.TFESC):
                                        byte = KISS.FESC
                                    escape = False
                                command_buffer = command_buffer+bytes([byte])
                                if (len(command_buffer) == 2):
                                    self.maj_version = int(command_buffer[0])
                                    self.min_version = int(command_buffer[1])
                                    self.validate_firmware()

                        elif (command == KISS.CMD_STAT_RX):
                            if (byte == KISS.FESC):
                                escape = True
                            else:
                                if (escape):
                                    if (byte == KISS.TFEND):
                                        byte = KISS.FEND
                                    if (byte == KISS.TFESC):
                                        byte = KISS.FESC
                                    escape = False
                                command_buffer = command_buffer+bytes([byte])
                                if (len(command_buffer) == 4):
                                    self.r_stat_rx = ord(command_buffer[0]) << 24 | ord(command_buffer[1]) << 16 | ord(command_buffer[2]) << 8 | ord(command_buffer[3])

                        elif (command == KISS.CMD_STAT_TX):
                            if (byte == KISS.FESC):
                                escape = True
                            else:
                                if (escape):
                                    if (byte == KISS.TFEND):
                                        byte = KISS.FEND
                                    if (byte == KISS.TFESC):
                                        byte = KISS.FESC
                                    escape = False
                                command_buffer = command_buffer+bytes([byte])
                                if (len(command_buffer) == 4):
                                    self.r_stat_tx = ord(command_buffer[0]) << 24 | ord(command_buffer[1]) << 16 | ord(command_buffer[2]) << 8 | ord(command_buffer[3])

                        elif (command == KISS.CMD_STAT_RSSI):
                            self.r_stat_rssi = byte-RNodeMultiInterface.RSSI_OFFSET
                        elif (command == KISS.CMD_STAT_SNR):
                            self.r_stat_snr = int.from_bytes(bytes([byte]), byteorder="big", signed=True) * 0.25
                            try:
                                sfs = self.r_sf-7
                                snr = self.r_stat_snr
                                q_snr_min = RNodeMultiInterface.Q_SNR_MIN_BASE-sfs*RNodeMultiInterface.Q_SNR_STEP
                                q_snr_max = RNodeMultiInterface.Q_SNR_MAX
                                q_snr_span = q_snr_max-q_snr_min
                                quality = round(((snr-q_snr_min)/(q_snr_span))*100,1)
                                if quality > 100.0: quality = 100.0
                                if quality < 0.0: quality = 0.0
                                self.r_stat_q = quality
                            except:
                                pass
                        elif (command == KISS.CMD_ST_ALOCK):
                            if (byte == KISS.FESC):
                                escape = True
                            else:
                                if (escape):
                                    if (byte == KISS.TFEND):
                                        byte = KISS.FEND
                                    if (byte == KISS.TFESC):
                                        byte = KISS.FESC
                                    escape = False
                                command_buffer = command_buffer+bytes([byte])
                                if (len(command_buffer) == 2):
                                    at = command_buffer[0] << 8 | command_buffer[1]
                                    self.subinterfaces[self.last_write_index].r_st_alock = at/100.0
                                    RNS.log(str(self)+" Radio reporting short-term airtime limit is "+str(self.r_st_alock)+"%", RNS.LOG_DEBUG)
                        elif (command == KISS.CMD_LT_ALOCK):
                            if (byte == KISS.FESC):
                                escape = True
                            else:
                                if (escape):
                                    if (byte == KISS.TFEND):
                                        byte = KISS.FEND
                                    if (byte == KISS.TFESC):
                                        byte = KISS.FESC
                                    escape = False
                                command_buffer = command_buffer+bytes([byte])
                                if (len(command_buffer) == 2):
                                    at = command_buffer[0] << 8 | command_buffer[1]
                                    self.subinterfaces[self.last_write_index].r_lt_alock = at/100.0
                                    RNS.log(str(self)+" Radio reporting long-term airtime limit is "+str(self.r_lt_alock)+"%", RNS.LOG_DEBUG)
                        elif (command == KISS.CMD_STAT_CHTM):
                            if (byte == KISS.FESC):
                                escape = True
                            else:
                                if (escape):
                                    if (byte == KISS.TFEND):
                                        byte = KISS.FEND
                                    if (byte == KISS.TFESC):
                                        byte = KISS.FESC
                                    escape = False
                                command_buffer = command_buffer+bytes([byte])
                                if (len(command_buffer) == 8):
                                    ats = command_buffer[0] << 8 | command_buffer[1]
                                    atl = command_buffer[2] << 8 | command_buffer[3]
                                    cus = command_buffer[4] << 8 | command_buffer[5]
                                    cul = command_buffer[6] << 8 | command_buffer[7]
                                    
                                    self.r_airtime_short      = ats/100.0
                                    self.r_airtime_long       = atl/100.0
                                    self.r_channel_load_short = cus/100.0
                                    self.r_channel_load_long  = cul/100.0
                        elif (command == KISS.CMD_STAT_PHYPRM):
                            if (byte == KISS.FESC):
                                escape = True
                            else:
                                if (escape):
                                    if (byte == KISS.TFEND):
                                        byte = KISS.FEND
                                    if (byte == KISS.TFESC):
                                        byte = KISS.FESC
                                    escape = False
                                command_buffer = command_buffer+bytes([byte])
                                if (len(command_buffer) == 10):
                                    lst = (command_buffer[0] << 8 | command_buffer[1])/1000.0
                                    lsr = command_buffer[2] << 8 | command_buffer[3]
                                    prs = command_buffer[4] << 8 | command_buffer[5]
                                    prt = command_buffer[6] << 8 | command_buffer[7]
                                    cst = command_buffer[8] << 8 | command_buffer[9]

                                    if lst != self.r_symbol_time_ms or lsr != self.r_symbol_rate or prs != self.r_preamble_symbols or prt != self.r_premable_time_ms or cst != self.r_csma_slot_time_ms:
                                        self.r_symbol_time_ms    = lst
                                        self.r_symbol_rate       = lsr
                                        self.r_preamble_symbols  = prs
                                        self.r_premable_time_ms  = prt
                                        self.r_csma_slot_time_ms = cst
                                        RNS.log(str(self)+" Radio reporting symbol time is "+str(round(self.r_symbol_time_ms,2))+"ms (at "+str(self.r_symbol_rate)+" baud)", RNS.LOG_DEBUG)
                                        RNS.log(str(self)+" Radio reporting preamble is "+str(self.r_preamble_symbols)+" symbols ("+str(self.r_premable_time_ms)+"ms)", RNS.LOG_DEBUG)
                                        RNS.log(str(self)+" Radio reporting CSMA slot time is "+str(self.r_csma_slot_time_ms)+"ms", RNS.LOG_DEBUG)
                        elif (command == KISS.CMD_RANDOM):
                            self.r_random = byte
                        elif (command == KISS.CMD_PLATFORM):
                            self.platform = byte
                        elif (command == KISS.CMD_MCU):
                            self.mcu = byte
                        elif (command == KISS.CMD_ERROR):
                            if (byte == KISS.ERROR_INITRADIO):
                                RNS.log(str(self)+" hardware initialisation error (code "+RNS.hexrep(byte)+")", RNS.LOG_ERROR)
                                raise IOError("Radio initialisation failure")
                            elif (byte == KISS.ERROR_TXFAILED):
                                RNS.log(str(self)+" hardware TX error (code "+RNS.hexrep(byte)+")", RNS.LOG_ERROR)
                                raise IOError("Hardware transmit failure")
                            else:
                                RNS.log(str(self)+" hardware error (code "+RNS.hexrep(byte)+")", RNS.LOG_ERROR)
                                raise IOError("Unknown hardware failure")
                        elif (command == KISS.CMD_RESET):
                            if (byte == 0xF8):
                                if self.platform == KISS.PLATFORM_ESP32:
                                    if self.online:
                                        RNS.log("Detected reset while device was online, reinitialising device...", RNS.LOG_ERROR)
                                        raise IOError("ESP32 reset")
                        elif (command == KISS.CMD_READY):
                            self.process_queue()
                        elif (command == KISS.CMD_DETECT):
                            if byte == KISS.DETECT_RESP:
                                self.detected = True
                            else:
                                self.detected = False
                        elif (command == KISS.CMD_INTERFACES):
                            command_buffer = command_buffer+bytes([byte])
                            if (len(command_buffer) == 2):
                                # add the interface to the back of the lists
                                self.subinterface_indexes.append(command_buffer[0])
                                self.subinterface_types.append(KISS.interface_type_to_str(command_buffer[1]))
                                command_buffer = b""
                        
                else:
                    time_since_last = int(time.time()*1000) - last_read_ms
                    if len(data_buffer) > 0 and time_since_last > self.timeout:
                        RNS.log(str(self)+" serial read timeout in command "+str(command), RNS.LOG_WARNING)
                        data_buffer = b""
                        in_frame = False
                        command = KISS.CMD_UNKNOWN
                        escape = False

                    if self.id_interval != None and self.id_callsign != None:
                        if self.first_tx != None:
                            if time.time() > self.first_tx + self.id_interval:
                                RNS.log("Interface "+str(self)+" is transmitting beacon data: "+str(self.id_callsign.decode("utf-8")), RNS.LOG_DEBUG)
                                # todo, fixme
                                self.processOutgoing(self.id_callsign)

                    sleep(0.08)

        except Exception as e:
            self.online = False
            RNS.log("A serial port error occurred, the contained exception was: "+str(e), RNS.LOG_ERROR)
            RNS.log("The interface "+str(self)+" experienced an unrecoverable error and is now offline.", RNS.LOG_ERROR)
            RNS.log(traceback.print_exc(), RNS.LOG_DEBUG)

            if RNS.Reticulum.panic_on_interface_error:
                RNS.panic()

            RNS.log("Reticulum will attempt to reconnect the interface periodically.", RNS.LOG_ERROR)

        self.online = False
        try:
            self.serial.close()
        except Exception as e:
            pass

        if not self.detached and not self.reconnecting:
            self.reconnect_port()

    def reconnect_port(self):
        self.reconnecting = True
        while not self.online and not self.detached:
            try:
                time.sleep(5)
                RNS.log("Attempting to reconnect serial port "+str(self.port)+" for "+str(self)+"...", RNS.LOG_VERBOSE)
                self.open_port()
                if self.serial.is_open:
                    self.configure_device()
            except Exception as e:
                RNS.log("Error while reconnecting port, the contained exception was: "+str(e), RNS.LOG_ERROR)

        self.reconnecting = False
        if self.online:
            RNS.log("Reconnected serial port for "+str(self))

    def detach(self):
        self.detached = True
        self.disable_external_framebuffer()

        # todo: make this iterate over all subinterfaces
        self.setRadioState(KISS.RADIO_STATE_OFF, 0)
        self.setRadioState(KISS.RADIO_STATE_OFF, 1)
        self.leave()

    def should_ingress_limit(self):
        return False

    def process_queue(self):
        for interface in self.subinterfaces:
            interface.process_queue()

    def __str__(self):
        return "RNodeMultiInterface["+str(self.name)+"]"

class RNodeSubInterface(Interface):
    MAX_CHUNK = 32768

    FREQ_MIN = 137000000
    FREQ_MAX = 3000000000

    RSSI_OFFSET = 157

    Q_SNR_MIN_BASE = -9
    Q_SNR_MAX      = 6
    Q_SNR_STEP     = 2

    def __init__(self, owner, parent_interface, index, interface_type, frequency = None, bandwidth = None, txpower = None, sf = None, cr = None, flow_control = False, st_alock = None, lt_alock = None,):
        if RNS.vendor.platformutils.is_android():
            raise SystemError("Invalid interface type. The Android-specific RNode interface must be used on Android")

        import importlib
        if importlib.util.find_spec('serial') != None:
            import serial
        else:
            RNS.log("Using the RNode interface requires a serial communication module to be installed.", RNS.LOG_CRITICAL)
            RNS.log("You can install one with the command: python3 -m pip install pyserial", RNS.LOG_CRITICAL)
            RNS.panic()

        super().__init__()
        
        match index:
            case 0:
                sel_cmd = KISS.CMD_SEL_INT0
                data_cmd= KISS.CMD_INT0_DATA
            case 1:
                sel_cmd = KISS.CMD_SEL_INT1
                data_cmd= KISS.CMD_INT1_DATA
            case 2:
                sel_cmd = KISS.CMD_SEL_INT2
                data_cmd= KISS.CMD_INT2_DATA
            case 3:
                sel_cmd = KISS.CMD_SEL_INT3
                data_cmd= KISS.CMD_INT3_DATA
            case 4:
                sel_cmd = KISS.CMD_SEL_INT4
                data_cmd= KISS.CMD_INT4_DATA
            case 5:
                sel_cmd = KISS.CMD_SEL_INT5
                data_cmd= KISS.CMD_INT5_DATA
            case 6:
                sel_cmd = KISS.CMD_SEL_INT6
                data_cmd= KISS.CMD_INT6_DATA
            case 7:
                sel_cmd = KISS.CMD_SEL_INT7
                data_cmd= KISS.CMD_INT7_DATA
            case 8:
                sel_cmd = KISS.CMD_SEL_INT8
                data_cmd= KISS.CMD_INT8_DATA
            case 9:
                sel_cmd = KISS.CMD_SEL_INT9
                data_cmd= KISS.CMD_INT9_DATA
            case 10:
                sel_cmd = KISS.CMD_SEL_INT10
                data_cmd= KISS.CMD_INT10_DATA
            case 11:
                sel_cmd = KISS.CMD_SEL_INT11
                data_cmd= KISS.CMD_INT11_DATA
            case _:
                sel_cmd = KISS.CMD_SEL_INT0
                data_cmd= KISS.CMD_INT0_DATA

        self.owner       = owner
        self.index       = index
        self.sel_cmd     = sel_cmd
        self.data_cmd    = data_cmd
        self.interface_type= interface_type
        self.flow_control= flow_control
        self.speed       = 115200
        self.databits    = 8
        self.stopbits    = 1
        self.timeout     = 100
        self.online      = False
        self.detached    = False
        self.reconnecting= False

        self.frequency   = frequency
        self.bandwidth   = bandwidth
        self.txpower     = txpower
        self.sf          = sf
        self.cr          = cr
        self.state       = KISS.RADIO_STATE_OFF
        self.bitrate     = 0
        self.st_alock    = st_alock
        self.lt_alock    = lt_alock
        self.platform    = None
        self.display     = None
        self.mcu         = None

        self.last_id     = 0
        self.first_tx    = None

        self.r_frequency = None
        self.r_bandwidth = None
        self.r_txpower   = None
        self.r_sf        = None
        self.r_cr        = None
        self.r_state     = None
        self.r_lock      = None
        self.r_stat_rx   = None
        self.r_stat_tx   = None
        self.r_stat_rssi = None
        self.r_stat_snr  = None
        self.r_st_alock  = None
        self.r_lt_alock  = None
        self.r_random    = None
        self.r_airtime_short      = 0.0
        self.r_airtime_long       = 0.0
        self.r_channel_load_short = 0.0
        self.r_channel_load_long  = 0.0
        self.r_symbol_time_ms = None
        self.r_symbol_rate = None
        self.r_preamble_symbols = None
        self.r_premable_time_ms = None

        self.packet_queue    = []
        self.interface_ready = False
        self.announce_rate_target = None
        self.parent_interface = parent_interface

        # add this interface to the subinterfaces array
        self.parent_interface.subinterfaces.insert(index, self)

        self.validcfg  = True
        if (self.frequency < RNodeSubInterface.FREQ_MIN or self.frequency > RNodeSubInterface.FREQ_MAX):
            RNS.log("Invalid frequency configured for "+str(self), RNS.LOG_ERROR)
            self.validcfg = False

        if (self.txpower < 0 or self.txpower > 22):
            RNS.log("Invalid TX power configured for "+str(self), RNS.LOG_ERROR)
            self.validcfg = False

        if (self.bandwidth < 7800 or self.bandwidth > 1625000):
            RNS.log("Invalid bandwidth configured for "+str(self), RNS.LOG_ERROR)
            self.validcfg = False

        if (self.sf < 5 or self.sf > 12):
            RNS.log("Invalid spreading factor configured for "+str(self), RNS.LOG_ERROR)
            self.validcfg = False

        if (self.cr < 5 or self.cr > 8):
            RNS.log("Invalid coding rate configured for "+str(self), RNS.LOG_ERROR)
            self.validcfg = False

        if (self.st_alock and (self.st_alock < 0.0 or self.st_alock > 100.0)):
            RNS.log("Invalid short-term airtime limit configured for "+str(self), RNS.LOG_ERROR)
            self.validcfg = False

        if (self.lt_alock and (self.lt_alock < 0.0 or self.lt_alock > 100.0)):
            RNS.log("Invalid long-term airtime limit configured for "+str(self), RNS.LOG_ERROR)
            self.validcfg = False

        if (not self.validcfg):
            raise ValueError("The configuration for "+str(self)+" contains errors, interface is offline")

        self.configure_device()

    def configure_device(self):
        self.r_frequency = None
        self.r_bandwidth = None
        self.r_txpower   = None
        self.r_sf        = None
        self.r_cr        = None
        self.r_state     = None
        self.r_lock      = None
        sleep(2.0)

        #thread = threading.Thread(target=self.readLoop)
        #thread.daemon = True
        #thread.start()

        #self.detect()
        #sleep(0.2)
        #
        #if not self.detected:
        #    RNS.log("Could not detect device for "+str(self), RNS.LOG_ERROR)
        #    self.serial.close()
        #else:
        #    if self.platform == KISS.PLATFORM_ESP32:
        #        self.display = True

        #RNS.log("Serial port "+self.port+" is now open")
        RNS.log("Configuring RNode subinterface "+str(self)+"...", RNS.LOG_VERBOSE)
        self.initRadio()
        if (self.validateRadioState()):
            self.interface_ready = True
            RNS.log(str(self)+" is configured and powered up")
            sleep(0.3)
            self.online = True
        else:
            RNS.log("After configuring "+str(self)+", the reported radio parameters did not match your configuration.", RNS.LOG_ERROR)
            RNS.log("Make sure that your hardware actually supports the parameters specified in the configuration", RNS.LOG_ERROR)
            RNS.log("Aborting RNode startup", RNS.LOG_ERROR)
            #self.serial.close()
            

    def initRadio(self):
        self.parent_interface.setFrequency(self.frequency, self.index)
        self.parent_interface.setBandwidth(self.bandwidth, self.index)
        self.parent_interface.setTXPower(self.txpower, self.index)
        self.parent_interface.setSpreadingFactor(self.sf, self.index)
        self.parent_interface.setCodingRate(self.cr, self.index)
        self.parent_interface.setSTALock(self.st_alock, self.index)
        self.parent_interface.setLTALock(self.lt_alock, self.index)
        self.parent_interface.setRadioState(KISS.RADIO_STATE_ON, self.index)
        self.state = KISS.RADIO_STATE_ON

    def validateRadioState(self):
        RNS.log("Waiting for radio configuration validation for "+str(self)+"...", RNS.LOG_VERBOSE)
        sleep(0.25);

        self.validcfg = True
        if (self.r_frequency != None and abs(self.frequency - int(self.r_frequency)) > 100):
            RNS.log("Frequency mismatch", RNS.LOG_ERROR)
            self.validcfg = False
        if (self.bandwidth != self.r_bandwidth):
            RNS.log("Bandwidth mismatch", RNS.LOG_ERROR)
            self.validcfg = False
        if (self.txpower != self.r_txpower):
            RNS.log("TX power mismatch", RNS.LOG_ERROR)
            self.validcfg = False
        if (self.sf != self.r_sf):
            RNS.log("Spreading factor mismatch", RNS.LOG_ERROR)
            self.validcfg = False
        if (self.state != self.r_state):
            RNS.log("Radio state mismatch", RNS.LOG_ERROR)
            self.validcfg = False

        if (self.validcfg):
            return True
        else:
            return False


    def updateBitrate(self):
        try:
            self.bitrate = self.r_sf * ( (4.0/self.r_cr) / (math.pow(2,self.r_sf)/(self.r_bandwidth/1000)) ) * 1000
            self.bitrate_kbps = round(self.bitrate/1000.0, 2)
            RNS.log(str(self)+" On-air bitrate is now "+str(self.bitrate_kbps)+ " kbps", RNS.LOG_VERBOSE)
        except:
            self.bitrate = 0

    def processIncoming(self, data):
        self.rxb += len(data)
        self.owner.inbound(data, self)
        self.r_stat_rssi = None
        self.r_stat_snr = None

    def processOutgoing(self,data):
        if self.online:
            if self.interface_ready:
                if self.flow_control:
                    self.interface_ready = False

                #if data == self.id_callsign:
                #    self.first_tx = None
                #else:
                if self.first_tx == None:
                    self.first_tx = time.time()
                self.txb += len(data)
                self.parent_interface.processOutgoing(data, self.data_cmd)
            else:
                self.queue(data)

    def queue(self, data):
        self.packet_queue.append(data)


    def process_queue(self):
        if len(self.packet_queue) > 0:
            data = self.packet_queue.pop(0)
            self.interface_ready = True
            self.processOutgoing(data)
        elif len(self.packet_queue) == 0:
            self.interface_ready = True

    def __str__(self):
        return self.parent_interface.name+"["+self.interface_type+":"+str(self.index)+"]"

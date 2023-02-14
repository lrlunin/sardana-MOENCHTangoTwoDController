# from sardana import DataAccess
from sardana.pool.controller import TwoDController
from tango import DeviceProxy, DevState
import numpy as np
from enum import Enum, IntEnum
from time import sleep

from sardana import State


# ReadOnly = DataAccess.ReadOnly
# ReadWrite = DataAccess.ReadWrite


class MOENCHTangoTwoDControllerZMQ(TwoDController):
    "This class is the Tango Sardana Two D controller for the MOENCH PSI"
    # ctrl_properties = {
    #     "controlMOENCHTangoFQDN": {
    #         Type: str,
    #         Description: "The FQDN of the MOENCH tango DS",
    #         DefaultValue: "rsxs/moenchControl/bchip286",
    #     },
    # }

    # class FrameMode(IntEnum):
    #     # hence detectormode in slsdet uses strings (not enums) need to be converted to strings
    #     # RAW = "raw"
    #     # FRAME = "frame"
    #     # PEDESTAL = "pedestal"
    #     # NEWPEDESTAL = "newPedestal"
    #     # NO_FRAME_MODE = "noFrameMode"
    #     RAW = 0
    #     FRAME = 1
    #     PEDESTAL = 2
    #     NEWPEDESTAL = 3
    #     NO_FRAME_MODE = 4

    # class DetectorMode(IntEnum):
    #     # hence detectormode in slsdet uses strings (not enums) need to be converted to strings
    #     # COUNTING = "counting"
    #     # ANALOG = "analog"
    #     # INTERPOLATING = "interpolating"
    #     # NO_DETECTOR_MODE = "noDetectorMode"
    #     COUNTING = 0
    #     ANALOG = 1
    #     INTERPOLATING = 2
    #     NO_DETECTOR_MODE = 3

    class TimingMode(IntEnum):
        # the values are the same as in slsdet.timingMode so no bidict table is required
        AUTO_TIMING = 0
        TRIGGER_EXPOSURE = 1

    # class DetectorSettings(IntEnum):
    #     # [G1_HIGHGAIN, G1_LOWGAIN, G2_HIGHCAP_HIGHGAIN, G2_HIGHCAP_LOWGAIN, G2_LOWCAP_HIGHGAIN, G2_LOWCAP_LOWGAIN, G4_HIGHGAIN, G4_LOWGAIN]
    #     G1_HIGHGAIN = 0
    #     G1_LOWGAIN = 1
    #     G2_HIGHCAP_HIGHGAIN = 2
    #     G2_HIGHCAP_LOWGAIN = 3
    #     G2_LOWCAP_HIGHGAIN = 4
    #     G2_LOWCAP_LOWGAIN = 5
    #     G4_HIGHGAIN = 6
    #     G4_LOWGAIN = 7

    """
    here are presented only key features and most significant parameters which are expected
    to be changed during the normal measurements

    as an example I took:
    https://github.com/desy-fsec/sardana-controllers/blob/master/python/twod/Pilatus.py
    """

    # axis_attributes = {
    #     "exposure": {
    #         Type: tango.DevFloat,
    #         Access: ReadWrite,
    #         Description: "exposure of each frame in s",
    #     },
    #     "delay": {
    #         Type: tango.DevFloat,
    #         Access: ReadWrite,
    #         Description: "delay after each trigger in s",
    #     },
    #     "timing_mode": {
    #         Type: tango.DevEnum,
    #         Access: ReadWrite,
    #         Description: "AUTO/TRIGGER exposure mode",
    #     },
    #     "triggers": {
    #         Type: tango.DevInt,
    #         Access: ReadWrite,
    #         Description: "expect this amount of triggers in the acquire session",
    #     },
    #     "filename": {
    #         Type: tango.DevString,
    #         Access: ReadWrite,
    #         Description: "filename prefix",
    #     },
    #     "filepath": {
    #         Type: tango.DevString,
    #         Access: ReadWrite,
    #         Description: "path to save files",
    #     },
    #     "fileindex": {Type: tango.DevInt, Access: ReadWrite, Description: "index "},
    #     "frames": {
    #         Type: tango.DevInt,
    #         Access: ReadWrite,
    #         Description: "amount of frames for each trigger to acquire",
    #     },
    #     "framemode": {
    #         Type: tango.DevEnum,
    #         Access: ReadWrite,
    #         Description: "framemode of detector [RAW, FRAME, PEDESTAL, NEWPEDESTAL]",
    #     },
    #     "detectormode": {
    #         Type: tango.DevEnum,
    #         Access: ReadWrite,
    #         Description: "detectorMode [COUNTING, ANALOG, INTERPOLATING]",
    #     },
    #     "highvoltage": {
    #         Type: tango.DevInt,
    #         Access: ReadWrite,
    #         Description: "bias voltage on sensor",
    #     },
    #     "period": {
    #         Type: tango.DevFloat,
    #         Access: ReadWrite,
    #         Description: "period for auto timing mode, need be at least exposure + 250us",
    #     },
    #     "gain_settings": {
    #         Type: tango.DevEnum,
    #         Access: ReadWrite,
    #         Description: "[G1_HIGHGAIN, G1_LOWGAIN, G2_HIGHCAP_HIGHGAIN, G2_HIGHCAP_LOWGAIN, G2_LOWCAP_HIGHGAIN, G2_LOWCAP_LOWGAIN, G4_HIGHGAIN, G4_LOWGAIN]",
    #     },
    #     "tiff_fullpath_next": {
    #         Type: tango.DevString,
    #         Access: ReadWrite,
    #         Description: "full path of the next capture",
    #     },
    #     "tiff_fullpath_last": {
    #         Type: tango.DevString,
    #         Access: ReadWrite,
    #         Description: "full path of the last capture",
    #     },
    #     "sum_image_last": {
    #         Type: ((tango.DevLong,),),
    #         Access: ReadOnly,
    #         Description: "last summarized 400x400 image from detector",
    #     },
    # }

    def __init__(self, inst, props, *args, **kwargs):
        """Constructor"""
        TwoDController.__init__(self, inst, props, *args, **kwargs)
        self._log.debug("MOENCHTangoTwoDControllerZMQ Initialization ...")
        self.control_device = DeviceProxy("rsxs/moenchControl/bchip286")
        self.zmq_server = DeviceProxy("rsxs/moenchZmqServer/bchip286")
        self._log.debug("Ping device...")
        self._log.debug("SUCCESS")
        self._axes = {}

    def AddDevice(self, axis):
        self._axes[axis] = {}

    def DeleteDevice(self, axis):
        self._axes.pop(axis)

    def ReadOne(self, axis):
        self._log.debug(f"Called ReadOne on axis {axis}")
        if axis == 0:
            return self.zmq_server.analog_img
        elif axis == 1:
            return self.zmq_server.analog_img_pumped
        elif axis == 2:
            return self.zmq_server.threshold_img
        elif axis == 3:
            return self.zmq_server.threshold_img_pumped
        elif axis == 4:
            return self.zmq_server.counting_img
        elif axis == 5:
            return self.zmq_server.counting_img_pumped

    def SetAxisPar(self, axis, parameter, value):
        pass
    
    # self.control_device.detector_status corresponds to
    # status_dict = {
    #     runStatus.IDLE: DevState.ON, -> ready
    #     runStatus.ERROR: DevState.FAULT,
    #     runStatus.WAITING: DevState.STANDBY, -> waiting for triggers
    #     runStatus.RUN_FINISHED: DevState.ON,
    #     runStatus.TRANSMITTING: DevState.RUNNING,
    #     runStatus.RUNNING: DevState.RUNNING, -> acquiring
    #     runStatus.STOPPED: DevState.ON,
    # }

    # zmq server corresponds to
    # if acquiring -> DevState.RUNNING
    # if ready -> DevState.ON

    def StateAll(self):
        self._log.debug("Called StateAll")

    def StateOne(self, axis):
        """Get the specified counter state"""
        self._log.debug(f"Called StateOne on axis {axis}")
        detector_state = self.control_device.detector_status
        zmq_server_state = self.zmq_server.state()

        self._log.debug(f"detector state: {detector_state}")
        self._log.debug(f"zmq server state: {zmq_server_state}")
        if detector_state == DevState.ON and zmq_server_state == DevState.ON:
            tup = (DevState.ON, "Camera ready")
        elif detector_state == DevState.FAULT or zmq_server_state == DevState.FAULT:
            tup = (DevState.FAULT, "Camera and/or zmq server in FAULT state")
        elif detector_state == DevState.STANDBY and zmq_server_state == DevState.RUNNING:
            tup = (DevState.MOVING, "Camera is waiting for trigger")
        elif detector_state == DevState.MOVING or zmq_server_state == DevState.RUNNING:
            tup = (DevState.MOVING, "Camera acquiring and/or zmq server process the data")
        self._log.debug(f"tup = {tup}")
        return tup

    def PrepareOne(self, axis, value, repetitions, latency, nb_starts):
        """
        value is a exposure in sec
        we need to set only up amount of triggers, TRIGGER_EXPOSURE mode and only 1 frame per trigger
        detectormode will not be changed
        """
        self._log.debug(f"Called PrepareOne on axis {axis}")
        if axis == 0:
            triggers = int(value * 100)
            self._log.debug("Set trigger to TRIGGER_EXPOSURE")
            self.control_device.timing_mode = self.TimingMode.TRIGGER_EXPOSURE
            self._log.debug("Set frames per trigger to 1")
            self.control_device.frames = 1
            self._log.debug(f"Set triggers to {triggers}")
            self.control_device.triggers = triggers
            self._log.debug("leaving PrepareOne")

    def LoadOne(self, axis, value, repetitions, latency):
        self._log.debug(f"Called LoadOne on axis {axis}")
        pass
    
    def LoadAll(self):
        self._log.debug("Called LoadAll")
        pass

    def StartOne(self, axis, value=None):
        """acquire the specified counter"""
        self._log.debug("Called StartOne")

    def StartAll(self):
        self._log.debug("Called StartAll")
        self.control_device.start_acquire()
        self._log.debug("sleep 1sec")
        sleep(3)
        self._log.debug("awake")
        self._log.debug("Leaving StartOne")

    def StopOne(self, axis):
        """Stop the specified counter"""
        if axis == 0:
            self._log.debug("Called StopOne")
            self.control_device.stop_acquire()

    def AbortOne(self, axis):
        """Abort the specified counter"""
        self._log.debug(f"Called AbortOne on axis {axis}")

    def AbortAll(self):
        self._log.debug(f"Called AbortAll")
        self.control_device.stop_acquire()
        self.zmq_server.abort_receiver()


    def GetAxisPar(self, axis, par):
        self._log.debug("Called GetAxisPar")
        if par == "shape":
            return [400, 400]
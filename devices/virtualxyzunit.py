"""
Manipulator class contains access to a manipulator and transformed coordinates.

TODO: raise exceptions if not calibrated
"""
from numpy import array, ones, zeros, eye, dot
from numpy.linalg import inv
from xyzunit import XYZUnit

__all__ = ['VirtualXYZUnit','CalibrationException']

class CalibrationException(Exception):
    def __init__(self, msg):
        self.msg = msg

class VirtualXYZUnit(XYZUnit): # could be a device
    def __init__(self, dev, stage):
        '''
        Parameters
        ----------
        dev : underlying XYZ unit
        stage : XYZ unit representing the stage
        '''
        self.dev = dev
        self.stage = stage
        self.memory = dict
        self.M = eye(3) # Matrix transform
        self.Minv = eye(3) # Inverse of M
        self.x0 = zeros(3) # Offset
        self.is_calibrated = False # calibration status

    def position(self, axis = None):
        '''
        Current position along an axis.

        Parameters
        ----------
        axis : axis number starting at 0

        Returns
        -------
        The current position of the device axis in um.
        '''
        y = self.dev.position()
        x = dot(self.M, y) + self.x0
        if axis is None:
            return x
        else:
            return x[axis]

    def absolute_move(self, x, axis = None):
        '''
        Moves the device axis to position x.

        Parameters
        ----------
        axis: axis number starting at 0
        x : target position in um.
        '''
        if axis is not None:
            x_target = x
            x = self.position()
            x[axis] = x_target
        self.dev.absolute_move(dot(self.Minv, x - self.x0))

    def relative_move(self, x, axis = None):
        '''
        Moves the device axis by relative amount x in um.

        Parameters
        ----------
        axis: axis number
        x : position shift in um.
        '''
        if axis is not None:
            x_target = x
            x = zeros(3)
            x[axis] = x_target
        self.dev.relative_move(dot(self.Minv, x))

    def secondary_calibration(self):
        '''
        Adjusts reference coordinate system assuming is centered on microscope view.
        '''
        self.x0 = self.stage.position() - dot(self.M, self.dev.position())

    def go(self):
        '''
        Go to current stage position.
        '''
        self.absolute_move(self.stage.position())

    def primary_calibration(self, x, y):
        '''
        x and y are two lists of 4 vectors, corresponding to 4 measurements in the
        stage and manipulator systems.
        '''
        dx = array(x).T
        dx = dx[:,1] - dx[:,0] # we calculate shifts relative to first position
        dy = array(y).T
        dy = dy[:, 1] - dy[:, 0]
        self.M = dot(dx, inv(dy))
        self.Minv=inv(self.M)
        self.x0 = x[0]-dot(self.M, y[0])
        self.is_calibrated = True

    def calibration_precision(self):
        '''
        Checks the precision of calibration, assuming the two reference systems are properly
        calibrated, i.e., values map to micrometers.

        Returns
        -------
        x, y, z: relative error in x, y and z axes of the stage system
        '''
        return [abs(1-(sum(self.M[i,:]**2))**.5) for i in range(3)]
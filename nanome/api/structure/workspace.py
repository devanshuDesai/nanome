from nanome._internal._structure._workspace import _Workspace
from nanome.util import Vector3, Quaternion, Matrix

from math import cos, sin

class Workspace(_Workspace):
    def __init__(self):
        _Workspace.__init__(self)
        self.transform = self._transform

    @property
    def complexes(self):
        return self._complexes
    @complexes.setter
    def complexes(self, value):
        self._complexes = value
    
    class Transform(_Workspace.Transform):
        @property
        def position(self):
            return self._position
        @position.setter
        def position(self, value):
            self._position = value

        @property
        def rotation(self):
            return self._rotation
        @rotation.setter
        def rotation(self, value):
            self._rotation = value
        
        @property
        def scale(self):
            return self._scale
        @scale.setter
        def scale(self, value):
            self._scale = value

        def get_absolute_to_relative_matrix(self):
            scale = Matrix(4, 4)
            scale[0][0] = self._scale.x
            scale[1][1] = self._scale.y
            scale[2][2] = self._scale.z

            rotation = Matrix.from_quaternion(self._rotation)

            translation = Matrix.identity(4)
            translation[0][3] = self._position.x
            translation[1][3] = self._position.y
            translation[2][3] = self._position.z

            transformation = translation * rotation * scale
            return transformation

        def get_relative_to_absolute_matrix(self):
            result = self.get_absolute_to_relative_matrix()
            return result.get_inverse()

    _Workspace.Transform._create = Transform
_Workspace._create = Workspace

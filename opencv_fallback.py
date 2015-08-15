import cv2
import numpy as np

class Camera:
	
    name            = "OpenCV Camera"
    uid             = 0
	
    def __init__(self, camera_id=0):
        self.cap = cv2.VideoCapture(camera_id)
        self.frame = None

        testframe = self.capture()
        self.width = testframe.shape[1]
        self.height = testframe.shape[0]


    def open(self):
        """Opens a particular camera. Returns the camera's handle"""
        return 0

    def close(self):
        """Closes a camera given a handle"""
        self.cap.release()

    def capture_start(self):
        """Begins Camera Capture"""
        return

    def capture_end(self):
        """Ends Camera Capture"""
        return 0

    def capture_query(self):
        """Checks if the camera is running"""
        return self.cap.isOpened()

    def queue_frame(self):
        # Queue the frame
        return self.cap.grab()

    def capture_wait(self):
        # Wait for the frame to complete
        ret, self.frame = self.cap.retrieve()

        return np.mean(self.frame, axis=2) # make monochrome

    def capture(self):
        """ Convenience function that automatically queues a frame, initiates capture
            and returns the image frame as a string"""

        self.queue_frame()

        image = self.capture_wait()
            
        # Return image string
        return image



    def attr_enum_set(self,param,value):
        """Set a particular enum attribute given a param and value"""
        return True

    def attr_enum_get(self,param):
        """Reads a particular enum attribute given a param"""
        return 0

    def command_run(self,command):
        """Runs a particular command valid in the Camera and Drive Attributes"""
        return True

    def attr_uint32_get(self,name):
        """Returns a particular integer attribute"""
        return 0

    def attr_uint32_set(self, param, value):
        """Sets a particular integer attribute"""
        return True

    def attr_float32_get(self,name):
        """Returns a particular integer attribute"""
        return 0.0

    def attr_float32_set(self, param, value):
        """Sets a particular integer attribute"""
        return True

    def attr_range_enum(self, param):
        return None

    def attr_range_uint32(self,name):
        """Returns a particular integer attribute"""
        return None

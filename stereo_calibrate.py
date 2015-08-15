#!/usr/bin/env python2
from pvapi import PvAPI, Camera
import time
# from psychopy import visual, event, core, monitors, logging, tools
from scipy.misc import imsave
import numpy as np
import multiprocessing as mp
import threading
from Queue import Queue
import sys
import errno
import os
import optparse
from stereovision.calibration import StereoCalibrator


parser = optparse.OptionParser()
parser.add_option('--output-path', action="store", dest="output_path", default="/tmp/frames", help="out path directory [default: /tmp/frames]")
parser.add_option('--output-format', action="store", dest="output_format", type="choice", choices=['png', 'npz'], default='png', help="out file format, png or npz [default: png]")
parser.add_option('--use-pvapi', action="store_true", dest="use_pvapi", default=True, help="use the pvapi")
parser.add_option('--use-opencv', action="store_false", dest="use_pvapi", help="use some other camera")
parser.add_option('--write-process', action="store_true", dest="save_in_separate_process", default=True, help="spawn process for disk-writer [default: True]")
parser.add_option('--write-thread', action="store_false", dest="save_in_separate_process", help="spawn threads for disk-writer")
parser.add_option('--frame-rate', action="store", dest="frame_rate", help="requested frame rate", type="float", default=60.0)
(options, args) = parser.parse_args()

acquire_images = True
save_images = True

output_path = options.output_path
output_format = options.output_format
save_in_separate_process = options.save_in_separate_process
frame_rate = options.frame_rate

use_pvapi = options.use_pvapi

save_as_png = False
save_as_npz = False
if output_format == 'png':
    save_as_png = True
elif output_format == 'npz':
    save_as_npz = True

# Make the output path if it doesn't already exist
try:
    os.mkdir(output_path)
except OSError, e:
    if e.errno != errno.EEXIST:
        raise e
    pass


import cv2
          
cv2.namedWindow('cam_window')
import numpy as np
r = np.random.rand(100,100)
cv2.imshow('cam_window', r)



# -------------------------------------------------------------
# Camera Setup
# -------------------------------------------------------------

camera = None

if acquire_images:

    print('Searching for camera...')


    # try PvAPI

    camera = None
    cameras = []
    cam_info = None

    if use_pvapi:

        pvapi_retries = 50

        # get the camera list
        
        print('Getting camera driver..')
        
        n = 0
        camera_driver = None
        while camera_driver is None and n < pvapi_retries:
            try:
                camera_driver = PvAPI(libpath='./')
            except Exception as e:
                print('.')
                time.sleep(0.1)
                camera_driver = None
                n += 1

        print('Getting camera object...')

        n = 0
        cam_info = None

        # Let it have a few tries in case the camera is waking up

        while cam_info is None and n < pvapi_retries:
            try:
                print('trying...')
                cameras = camera_driver.camera_list()
                cam_info = cameras[0]
                n += 1
                print '.'
                time.sleep(0.5)

                if cameras[0].UniqueId == 0L:
                    raise Exception('No cameras found')
                time.sleep(0.5)
                camera = Camera(camera_driver, cameras[0])

                print("Bound to PvAPI camera (name: %s, uid: %s)" % (camera.name, camera.uid))

                camera.request_frame_rate(frame_rate)

            except Exception as e:

                print("Unable to find PvAPI camera: %s" % e)
                cam_info = None


    if camera is None:
        try:
            import opencv_fallback

            camera = opencv_fallback.Camera(0)

            print("Bound to OpenCV fallback camera.")
        except Exception as e2:
            print("Could not load OpenCV fallback camera")
            print e2
            exit()


# -------------------------------------------------------------
# Set up a thread to write stuff to disk
# -------------------------------------------------------------

if save_in_separate_process:
    im_queue = mp.Queue()
else:
    im_queue = Queue()

disk_writer_alive = True

def save_images_to_disk():
    print('Disk-saving thread active...')
    n = 0
    while disk_writer_alive: 
        if not im_queue.empty():
            
            try:
                im_array, metadata = im_queue.get()
            except e as Exception:
                break

            if im_array is None:
                break

            name = "%s_%d" % (metadata['side'], metadata['frame_number'])

            print im_array.shape
            if save_as_png:
                imsave('%s/%s.png' % (output_path, name), im_array)
            else:
                np.savez_compressed('%s/%s.npz' % (output_path, name), im_array)
            n += 1
    print('Disk-saving thread inactive...')


if save_in_separate_process:
    disk_writer = mp.Process(target=save_images_to_disk)
else:
    disk_writer = threading.Thread(target=save_images_to_disk)

# disk_writer.daemon = True

if save_images:
    disk_writer.daemon = True
    disk_writer.start()



nframes = 0
frame_accumulator = 0
t = 0
last_t = None

report_period = 60 # frames

if acquire_images:
    # Start acquiring
    camera.capture_start()
    camera.queue_frame()


# -------------------------------------------------------------
# Stereo calibrator
# -------------------------------------------------------------

# # take a test image
# im_array = camera.capture_wait()
# camera.queue_frame()

# calibrator = StereoCalibrator(3, 4, 1.0,)


while True:

    t = time.time()

    if acquire_images:
        im_array, _meta = camera.capture_wait()
        camera.queue_frame()

        nframes += 1

        # cut image in half
        shape = im_array.shape
        midpoint = shape[1] / 2
        left = (im_array[:, 0:midpoint] / 2**4).astype(np.uint8)
        right = (im_array[:, midpoint:-1] / 2**4).astype(np.uint8)

        # print left.min()
        # print left.max()

        # attempt to find corners
        found_left, corners_left = cv2.findChessboardCorners(left, (3, 4))
        found_right, corners_right = cv2.findChessboardCorners(right, (3, 4))

        print("l: %s, r: %s" % (found_left, found_right))

        if save_images and found_left and found_right:
            im_queue.put((left.copy(), dict(side='left', frame_number=nframes)))
            im_queue.put((right.copy(), dict(side='right', frame_number=nframes)))

        if found_left and found_right:
            cv2.drawChessboardCorners(left, (3,4), corners_left, found_left)
        cv2.imshow('cam_window', left)
        cv2.waitKey(2)



    if nframes % report_period == 0:
        if last_t is not None:
            print('avg frame rate: %f' % (report_period / (t - last_t)))
        last_t = t

    # Break out of the while loop if these keys are registered
    # if event.getKeys(keyList=['escape', 'q']):
    #     break

    # if nframes > 50:
    #     break


if acquire_images:
    camera.capture_end()
    camera.close()

if im_queue is not None:
    im_queue.put(None)

if save_images:
    hang_time = time.time()
    nag_time = 0.05

    sys.stdout.write('Waiting for disk writer to catch up (this may take a while)...')
    sys.stdout.flush()
    waits = 0
    while not im_queue.empty():
        now = time.time()
        if (now - hang_time) > nag_time:
            sys.stdout.write('.')
            sys.stdout.flush()
            hang_time = now
            waits += 1

    print waits
    print("\n")

    if not im_queue.empty():
        print("WARNING: not all images have been saved to disk!")

    disk_writer_alive = False

    if save_in_separate_process and disk_writer is not None:
        print("Terminating disk writer...")
        disk_writer.join()
        # disk_writer.terminate()
    
    # disk_writer.join()
    print('Disk writer terminated')        


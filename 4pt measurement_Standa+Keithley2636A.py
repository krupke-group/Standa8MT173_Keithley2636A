from keithley2600 import Keithley2600
import numpy as np
from matplotlib import pyplot as plt
from ctypes import *
import math
import pandas as pd
from matplotlib.animation import FuncAnimation 
import csv
import time
import os
import sys
import tempfile
import re
if sys.version_info >= (3,0):
    import urllib.parse
try:
    from pyximc import *
except ImportError as err:    
    print ("Can't import pyximc module. The most probable reason is that you haven't copied pyximc.py to the working directory. See developers' documentation for details.")
    exit()
except OSError as err:
    print ("Can't load libximc library. Please add all shared libraries to the appropriate places (next to pyximc.py on Windows). It is decribed in detail in developers' documentation. On Linux make sure you installed libximc-dev package.")
    exit()


x_movement= []                                            #array for storing x movement 
strain= []                                                #array for storing strain 
device_id = 0                                             # initialising translation stage devices
device_id_1 = 0


#for .csv file creation
fieldnames = ["x_movement", "Four_pt_Voltage", "Current", "Four_pt_Resistance", "Two_pt_Voltage", "Two_pt_Resistance" ]

with open('C31_NCG_glass.csv', 'w') as csv_file:
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    csv_writer.writeheader()
    
#function for reading x position of translation stage

def test_get_position(lib, device_id):                    
    x_pos = get_position_t()
    result = lib.get_position(device_id, byref(x_pos))
    return x_pos.Position

# function for movement settings of translation stages 

def MoveSettings(lib, device_id, Speed, uSpeed, Accel, Decel, AntiplaySpeed, uAntiplaySpeed): 
    x_move = move_settings_t()
    x_move.Speed = Speed
    x_move.uSpeed = uSpeed
    x_move.Accel = Accel
    x_move.Decel = Decel
    x_move.AntiplaySpeed = AntiplaySpeed
    x_move.uAntiplaySpeed = uAntiplaySpeed
    result = lib.set_move_settings(device_id, byref(x_move))
    
    
    


#Movement control of  the translation stage devices
def StageMovement(lib, device_id, device_id_1, Step_Size, Waiting_Time):
        
    lib.command_movr(device_id,Step_Size,0)             # command movr ( device_id, int DeltaPosition, int uDeltaPosition )
    #lib.command_movr(device_id_1,Step_Size,0)  
    x = test_get_position(lib,device_id)               # reading value of x each time
    print (x)
    lib.command_wait_for_stop(device_id, Waiting_Time) # command wait for stop ( device t id, uint32 t refresh interval ms )
    #lib.command_wait_for_stop(device_id_1, Waiting_Time)
    x_movement.append(x)                            # ading value of x each time into array
    
    return x
    

#connecting translation stage 
def TranslationStageConnect():
    devenum = lib.enumerate_devices(EnumerateFlags.ENUMERATE_PROBE, None)
    print("Device enum handle: " + repr(devenum))
    print("Device enum handle type: " + repr(type(devenum)))
    open_name = lib.get_device_name(devenum, 0)
    open_name_1 = lib.get_device_name(devenum, 1)
    if type(open_name) is str:
        open_name = open_name.encode()
    if type(open_name_1) is str:
        open_name_1= open_name_1.encode()
        
    print("\nOpen device " + repr(open_name))
    print("\nOpen device " + repr(open_name_1))
    device_id = lib.open_device(open_name)
    device_id_1= lib.open_device(open_name_1)
    print("Device id: " + repr(device_id))
    print("Device id: " + repr(device_id_1))

#Current sweep using keithley
def CurrentValue(self, smu1, current,t_int ,delay,n_pts, x_move):
    #keithley.reset()
    # input checks
    self._check_smu(smu1)
    
    # set state to busy
    self.busy = True
    # Define lists containing results. If we abort early, we have something to return.
    v_smu= []
    i_smu= []
    r_smu= []
    
    # CONFIGURE INTEGRATION TIME FOR EACH MEASUREMENT
    #self.setIntegrationTime(smu1, t_int)
    
    # SETUP  ARM counts
    # arm count = number of times the measurement is repeated (default set to 1)
    smu1.trigger.arm.count = n_pts 
   
    
    #Delay time time for measurement
    smu1.measure.delay = delay
  
    
    smu1.source.func = smu1.OUTPUT_DCAMPS
  
    
    #smu1.measure.autozero = smu1.AUTOZERO_AUTO
    
    
    #smu1.measure.autorangev = smu1.AUTORANGE_ON
    smu1.measure.rangev = 5
   
    smu1.measure.autorangei = smu1.AUTORANGE_ON
    #smu1.measure.nplc = 2


    
    smu1.source.rangev = 20
    smu1.source.rangei = 500e-9
  
    
    # display voltage values during measurement
    self.display.smua.measure.func = self.display.MEASURE_DCAMPS
   
    
    smu1.source.output= smu1.OUTPUT_ON

   
    #  for constant current from smua
    smu1.source.leveli= current # set current value 
    i_smu.append(current)      # adding current value to array i_smu
    
    smu1.sense = smu1.SENSE_REMOTE       # (SENSE_REMOTE for 4-wire)
    fourptvolt = smu1.measure.v()
    smu1.sense = smu1.SENSE_LOCAL         # (SENSE_REMOTE for 2-wire)
    twoptvolt = smu1.measure.v()
    fourptres = fourptvolt/current      # calcualting 4 point  resistance 
    twoptres = twoptvolt/current      # calculating 2 point resistacne
    
    #smu1.source.output= smu1.OUTPUT_OFF
    
    with open('C31_NCG_glass.csv', 'a') as csv_file:
        csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        info = {
            "x_movement" : x_move,
            "Four_pt_Voltage" : fourptvolt,
            "Current" : current,
            "Four_pt_Resistance" : fourptres,
            "Two_pt_Voltage" : twoptvolt,
            "Two_pt_Resistance" : twoptres
        }

        csv_writer.writerow(info)

    return v_smu, i_smu
    
    
if __name__ == '__main__':
    TranslationStageConnect()
    keithley = Keithley2600('TCPIP0::141.52.144.159::INSTR')
    keithley.reset()
    keithley.smua.measure.nplc = 15
    

    
    start =0
    stop = 500
    datapts = 100
    stepsize = math.floor((abs(start-stop))/datapts)
 
    waitingtime = 100
    MoveSettings(lib,1,1000,0,400,4,0,0)
    MoveSettings(lib,2,1000,0,400,4,0,0)
  
    for move in np.linspace(start,stop,datapts):
        x_move = StageMovement(lib,1,2, stepsize, waitingtime)
        #time.sleep(0.1)
        CurrentValue(keithley,keithley.smua,5e-10,10,1,0.5, x_move)
        
        #time.sleep(1)
    
    for move in np.linspace(start,stop,datapts):
        x_move = StageMovement(lib,1,2, -stepsize, waitingtime)
        CurrentValue(keithley,keithley.smua,1e-6,100,1,0.5, x_move)
        #time.sleep(1)
    

    keithley.reset()
    keithley.exit()
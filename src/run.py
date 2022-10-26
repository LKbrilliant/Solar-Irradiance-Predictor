#!/usr/bin/env python3
# Project:  Solar Irradiance Predictor
# Code by:  Anuradha Gunawardhana (@LKBrilliant)
# Data:     2022.10.19
# Version:  0.1.0
# Details:  
#
# Modules:  INA226 Voltage/Current measurement unit : https://github.com/e71828/pi_ina226
#           DS3231 Real time clock                  : https://github.com/switchdoclabs/RTC_SDL_DS3231
#           QMC5883 Magnetometer                    : https://github.com/texperiri/GY-271-QMC5883
#           Raspberry-pi camera (wide-angle)        : picamera

from ina226 import INA226
from qmc5883 import QMC5883
import SDL_DS3231
from gpiozero import LED
from picamera import PiCamera
import os
import sys
import time
import numpy as np

frameDelay = 10     # Period between two frame
batch_size = 50     # Number of data lines stored in the buffer before writing to the csv file

relay = LED(4)
relayON = False

data_collection_Start_hour = 6
data_collection_Stop_hour = 18

ds3231 = SDL_DS3231.SDL_DS3231(1, 0x68)
# ds3231.write_now() # Write the current time to the RTC
# seconds [0,59], minutes [0,59], hours [0,23], day [0,7], date [1-31], month [1-12], year [0-99].
# ds3231.write_all(00,51,9,2,25,10,22,save_as_24h=True)

magOffset =-108 # correction to align north to x axis
compass = QMC5883(xOffset = -1168.5 , yOffset = -800.0 , zOffset = 1762.5)

picam = PiCamera()
picam.led = True # turn off the camera led
picam.resolution = (2592, 1944)
picam.iso = 20
picam.shutter_speed = 200 # in microseconds

dataDir = '/media/pi/usb-stick/solar/data/'

def appendToCSV(filePath,data):
    with open(filePath, 'a') as f:
        np.savetxt(f, data,delimiter=',',fmt='%s')
        f.close()
    outputMsg('Buffer saved to the CSV')


def getCompassData():
    (dataReady,dataOverflow,dataSkippedForReading) = compass.status()
    if (dataReady == 1): 
        (x,y,z,rotX,rotY,rotZ) = compass.heading()
        compass_temp = compass.getTemperature()
        heading = rotZ + magOffset
    else: outputMsg('Error: Compass data is not ready')
    return compass_temp, heading

def getDateTime(dateSeparator,timeSeparator):
    _dateTime = ds3231.read_datetime()
    RTC_date = _dateTime.strftime("%Y{}%m{}%d".format(dateSeparator,dateSeparator))   # Select and format only the date from the datatime object
    RTC_time = _dateTime.strftime("%H{}%M{}%S".format(timeSeparator,timeSeparator))
    return RTC_date, RTC_time

def outputMsg(t):
    RTC_date, RTC_time = getDateTime('-',':')
    print('[{} {}]: {}'.format(RTC_date, RTC_time,t))

def main():
    i = 0
    v = 0
    global relayON
    ina = INA226(busnum=1, max_expected_amps=25)
    ina.configure()
    ina.set_low_battery(5)
    time.sleep(3)

    buffer = []
    outputMsg('Initialization Complete')

    _,current_time = getDateTime('-',':')
    hour = int(current_time[:2])
    print(hour)

    while True:
        while (hour < data_collection_Start_hour and hour > data_collection_Start_hour):
            outputMsg('Waiting for the')
            time.sleep(10)

        ina.wake(3)
        time.sleep(frameDelay)
        if relayON: 
            relay.off()
            relayON = False
            if ina.is_conversion_ready(): i = ina.current()
                
        else: 
            relay.on()
            relayON = True
            if ina.is_conversion_ready(): v = ina.voltage()

        RTC_date, RTC_time = getDateTime('-','_')
        if (int(RTC_date[:4]) < 2022):
            outputMsg('ERROR: Please reset the time of the the RTC module!')
            outputMsg('Program exit')
            break
        compass_temp, heading = getCompassData()

        imagePath = dataDir + RTC_date
        csvPath = imagePath + '/' + RTC_date + '.csv'

        if (not os.path.exists(imagePath)): os.makedirs(imagePath)      # Create a directory for each new day
        if (not os.path.exists(csvPath)): open(csvPath, "w")            # Create new CSV for each new day

        picam.capture(dataDir+'{}/{}.jpg'.format(RTC_date,RTC_time))    # Capture one image

        # sys.stdout.write("\r{} - {} - Power:{:.3f}W - Temp:{:.2f}°C - Heading:{:3.0f}° - Length of r:{}".format(RTC_date, RTC_time, i*v/1000, compass_temp, heading,len(r)))
        # sys.stdout.flush()
        
        buffer.append('{}, {:.3f}, {:.2f}, {}\r'.format(RTC_time, i*v/1000, compass_temp, heading))

        if (len(buffer) >= batch_size): 
            appendToCSV(csvPath,buffer)
            buffer = []



if __name__ == "__main__":
    main()

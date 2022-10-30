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
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime as dt
import matplotlib.dates as mdates
import threading

frameDelay = 10     # Period between two frame
batch_size = 50     # Number of data lines stored in the buffer before writing to the csv file

relay = LED(4)
relayON = False

status = "None"

data_collection_Start_hour = 6
data_collection_Stop_hour = 18

dataDir = '/media/pi/usb-stick/solar/data/'
scriptPath = '/home/pi/solar/Solar-Irradiance-Predictor/src'

ds3231 = SDL_DS3231.SDL_DS3231(1, 0x68)
# ds3231.write_now() # Write the current time to the RTC
# seconds [0,59], minutes [0,59], hours [0,23], day [0,7], date [1-31], month [1-12], year [0-99].
# ds3231.write_all(00,51,9,2,25,10,22,save_as_24h=True)

magOffset =-108 # correction to align north to x axis
compass = QMC5883(xOffset = -1168.5 , yOffset = -800.0 , zOffset = 1762.5)

def getDateTime(dSep,tSep):
    try:
        _dateTime = ds3231.read_datetime()
    except Exception as e:
        # cannot use the same error logging function because it uses the getDateTime
        status=f'Error: Real-Time-Clock reading failed ---- Exception: {e}'
        with open(f'{dataDir}/log.txt', 'a+') as f:
            f.write(status)
        print(status)
        return
    RTC_date = _dateTime.strftime(f'%Y{dSep}%m{dSep}%d')   # Select and format only the date from the datatime object
    RTC_time = _dateTime.strftime(f'%H{tSep}%M{tSep}%S')
    return RTC_date, RTC_time

def outputMsg(msg):
    global status
    RTC_date, RTC_time = getDateTime('-',':')
    status = f'[{RTC_date} {RTC_time}]: {msg}\n'
    with open(f'{dataDir}/log.txt', 'a+') as f:
        f.write(status)
    print(status)

try:
    picam = PiCamera()
    picam.led = True # turn off the camera led
    picam.resolution = (2592, 1944)
    picam.iso = 20
    picam.shutter_speed = 200 # in microseconds
except Exception as e:
    outputMsg(f'Error: Initiating PiCamera failed ---- Exception: {e}')

def makeTheGraph():
    threading.Timer(900,makeTheGraph).start()
    today, _ = getDateTime('-','_')
    headers = ['Time','Power','Temperature','Heading']
    path = f'{dataDir}{today}/{today}.csv'
    if (os.path.exists(path)):
        df = pd.read_csv(path,names=headers)
        df['Time'] = pd.to_datetime(df['Time'], format='%H_%M_%S')
        x = df['Time']
        y = df['Power']
        plt.figure(figsize=(10,4))
        plt.fill_between(x, y, color="skyblue", alpha=0.4)
        plt.plot(x, y, color="Slateblue",alpha=0.8, linewidth=1)
        plt.xlabel("Time (h)",size=12)
        plt.ylabel("Power (W)",size=12)
        plt.title(f'Solar Power Generation: {today}',size=20)
        plt.ylim(bottom=0)
        plt.gcf().autofmt_xdate()
        myFmt = mdates.DateFormatter('%H:%M')
        plt.gca().xaxis.set_major_formatter(myFmt)
        try:
            plt.savefig(f'{scriptPath}/plot.png', dpi=300, format='png', bbox_inches='tight')
        except Exception as e:
            outputMsg(f'Error: Plot saving failed ---- Exception: {e}')
        outputMsg('Graph: Plot saved')
    else:
        outputMsg(f'Error: Plotting failed --- No CSV file in the directory')

def appendToCSV(filePath,data):
    with open(filePath, 'a') as f: # 'a' = Append
        np.savetxt(f, data,delimiter=',',fmt='%s')
    outputMsg('Buffer saved to the CSV')
    with open(filePath, 'r') as fp: lines = len(fp.readlines()) # Read
    return lines

def logTail(numberOfLines):
    tail = ''
    with open(f'{dataDir}/log.txt', 'r') as f:
        for line in (f.readlines() [-numberOfLines:]):
            tail = tail +'<br>'+ line
        tail = tail[4:] # remove the initial blank space 
    return tail

def getCompassData():
    try:
        (dataReady,dataOverflow,dataSkippedForReading) = compass.status()
    except Exception as e:
        outputMsg(f'Error: Compass data reading failed  ---- Exception: {e}')
        return
    if (dataReady == 1): 
        (x,y,z,rotX,rotY,rotZ) = compass.heading()
        compass_temp = compass.getTemperature()
        heading = rotZ + magOffset
        return compass_temp, heading
    else: outputMsg('Error: Compass data is not ready')

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
    outputMsg('Data Collection Started')
    makeTheGraph() # Start the periodic plotting function
    try:
        while True:
            while (not(data_collection_Start_hour <= hour and hour <= data_collection_Stop_hour)):
                outputMsg('Waiting for the schedule')
                time.sleep(30)
            
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
            try:
                compass_temp, heading = getCompassData()
            except Exception as e:
                outputMsg(f'Error: Compass data reading failed ---- Exception: {e}')

            imagePath = f'{dataDir}{RTC_date}'
            csvPath = f'{imagePath}/{RTC_date}.csv'

            if (not os.path.exists(imagePath)): os.makedirs(imagePath)      # Create a directory for each new day
            if (not os.path.exists(csvPath)): open(csvPath, "w")            # Create new CSV for each new day

            try:
                picam.capture(f'{imagePath}/{RTC_time}.jpg')    # Capture one image
            except Exception as e:
                outputMsg(f'Error: Capturing from PiCamera failed ---- Exception: {e}')
            # sys.stdout.write("\r{} - {} - Power:{:.3f}W - Temp:{:.2f}°C - Heading:{:3.0f}° - Length of r:{}".format(RTC_date, RTC_time, i*v/1000, compass_temp, heading,len(r)))
            # sys.stdout.flush()
            try:
                buffer.append(f'{RTC_time}, {i*v/1000:.3f}, {compass_temp:.2f}, {heading}\r')
            except Exception as e:
                outputMsg(f'Error: Appending to buffer failed ---- Exception: {e}')

            if (len(buffer) >= batch_size): 
                lineCount = appendToCSV(csvPath,buffer)
                buffer = []
                today, _ = getDateTime('-','_')
                tail = logTail(10)
                with open(f'{scriptPath}/index.html',"w") as f:
                    f.write(f'<!DOCTYPE html><head><meta http-equiv="refresh" content="30"/><meta http-equiv="X-UA-Compatible" content="IE=edge"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Solar Status</title></head><body style="text-align:center; width: 100%; height: 100%;"><h1>Solar Data Collection Status</h1><h3>Page loading correctly means the Raspberry Pi running.</h3><h4>{today}: Current data count for - {lineCount} </h4><img src="plot.png" alt="Plot" width="70%" height="70%"><h3 >Last log entries:</h3><table style="margin: 0px auto;border: 2px solid black; width:50%"><tr><td style="text-align:left;padding-left: 5px;font: 12px monospace;">{tail}</td></tr></table></body></html>')
                    f.close()
    except Exception as e:
        outputMsg(f'Fatal Error withing the main loop ---- Exception: {e}')
if __name__ == "__main__":
    main()

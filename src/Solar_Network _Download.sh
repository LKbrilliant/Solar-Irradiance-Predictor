#!/bin/bash

remoteDataDir='/media/pi/usb-stick/solar/data/'
lcoalDataDir='/media/anuradha/Volume_A/Anuradha/Projects/Solar_Prediction/Src/Data/'


echo "Connecting to Raspberrypi...."
ssh pi@raspberrypi.local << EOF
cd /media/pi/usb-stick/solar/data
echo ""
echo "------- Available data folders --------"
ls
echo "---------------------------------------"
echo ""
EOF
read -p "Please enter the directory name you want to download: " dirName
read -p "Press 'y' to download the directory ($dirName): " downloadAnswer
if [ "$downloadAnswer" == "y" ]; 
then
    echo "Downloading..."
    #scp -r pi@raspberrypi.local:/media/pi/usb-stick/solar/data/$dirName /media/anuradha/Volume_A/Anuradha/Projects/Solar_Prediction/Data/$dirName
    scp -r pi@raspberrypi.local:$remoteDataDir$dirName $lcoalDataDir$dirName
    
    echo "Connecting to the RaspberryPi"
    echo ""
    read -p "Please 'y' if you want to remove the directory ($dirName): " removeAnswer
    if [ "$removeAnswer" == "y" ]; 
    then
        echo "Please enter raspberry pi login credentials to remove the directory"
        ssh pi@raspberrypi.local "sudo rm -r /media/pi/usb-stick/solar/data/$dirName"
        echo "Done Removing"
    else
        echo "Did not remove the downloaded directory"
    fi
else
    echo "Did not download any directories: \"Please check the directory name\""
fi
echo "--- Program End ---"
exit

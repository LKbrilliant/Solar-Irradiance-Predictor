# Solar-Irradiance-Predictor
- (WIP) This repository consist the code for irradiance data collection using a raspberry pi camera and a solar 20W panel


# Notes - Data Collector
## Autorun the python script - `sudo crontab -e`
  
  > `@reboot sudo python3 /home/pi/solar/Solar-Irradiance-Predictor/src/run.py &`

  > `@reboot cd /home/pi/solar/Solar-Irradiance-Predictor/src && sudo python -m http.server 8000 &`

## Auto mount usb at `usb-stick`
  > `sudo mkdir /media/pi/usb-stick`

  > `sudo mount /dev/sda1 /media/pi/usb-stick`
  
  > `sudo nano /etc/fstab`
  
  > `UUID=0523-7888 /media/pi/usb-stick auto defaults,nofail`
  
  > get the UUID = `sudo blkid -p /dev/sda1`
  
## Kill all python processors
  > `sudo pkill python`

## FFMPG Script
  > rename images as `img-####.jpg`
  
  > `ffmpeg -r 15 -i img-%04d.jpg -pix_fmt yuv420p video.mp4`

## Secure Copy - network download
  > `scp -r pi@raspberrypi.local:/media/pi/usb-stick/solar/data/2022-11-24 2022-11-24`

## Rsync
  > `rsync -avz -e ssh pi@raspberrypi.local:/media/pi/usb-stick/solar/data/ /home/anuradha/Desktop/data/`

# Notes - Proprocessing and model training

- `TimeDistributed` layer requires TF>=2.10
-  tensorflow gpu package on the conda is only 2.4 (2023-01-11)

| Test | nos_frames | Leap | fps | Categories | #clips_per_date | dates | img_rescale_ratio |     model      | video_rescale |    epochs    | Accurecy(max) | RAM Usage |
|:----:|:----------:|:----:|:---:|:----------:|:---------------:|:-----:|:-----------------:|:--------------:|:-------------:|:-------------|:-------------:|:---------:|
|  01  |     20     |  20  |  12 |     5      |       500       |   10  |       0.2         | EfficientNetB0 |   (255,255)   |   10(ES-6)   |     0.60      |   <32GB   |
|  02  |     20     |  20  |  12 |     5      |       500       |   16  |       0.2         | EfficientNetB0 |   (255,255)   |      10      |     0.70      |    43GB   |
|  03  |     15     |  15  |  15 |     3      |       500       |   22  |       0.2         | EfficientNetB0 |   (255,255)   |      10      |     0.55      |    20GB   |
|  04  |     20     |  20  |  12 |     3      |       500       |   23  |       0.2         | EfficientNetB0 |   (255,255)   |      10      |           |       |

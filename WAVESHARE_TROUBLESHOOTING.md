# Waveshare Display Troubleshooting Guide

## Common Waveshare 1024x600 Display Issues

### 1. Display Shows Wrong Resolution

**Symptoms:**
- Display is stretched, squished, or has black borders
- Resolution doesn't match 1024x600

**Solution:**
```bash
cd /home/pi/office_kiosk
sudo ./setup_waveshare.sh
sudo reboot
```

**Manual Fix:**
Add these lines to `/boot/config.txt`:
```
hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=87
hdmi_cvt 1024 600 60 6 0 0 0
disable_overscan=1
```

### 2. Touchscreen Not Working

**Symptoms:**
- Display works but touch input is not detected
- Touch works but coordinates are wrong

**Solution:**
```bash
# Enable I2C and SPI
sudo raspi-config
# Navigate to: Interface Options -> I2C -> Enable
# Navigate to: Interface Options -> SPI -> Enable

# Test touch detection
xinput list

# Calibrate touch
sudo /usr/local/bin/calibrate_touch.sh
```

### 3. Touch Coordinates Inverted/Rotated

**Symptoms:**
- Touch input is inverted (up is down, left is right)
- Touch works but offset from cursor

**Solution:**
Edit `/etc/X11/xorg.conf.d/99-waveshare-touch.conf`:
```
Section "InputClass"
    Identifier "Touchscreen"
    MatchIsTouchscreen "on"
    Driver "evdev"
    Option "Calibration" "0 1023 0 599"
    Option "SwapAxes" "0"        # Change to "1" if X/Y swapped
    Option "InvertX" "0"         # Change to "1" if X inverted
    Option "InvertY" "0"         # Change to "1" if Y inverted
EndSection
```

### 4. Display Upside Down or Rotated

**Symptoms:**
- Display is rotated 90°, 180°, or 270°

**Solution:**
Add to `/boot/config.txt`:
```
# Rotate 90 degrees clockwise
display_rotate=1

# Rotate 180 degrees
display_rotate=2

# Rotate 270 degrees clockwise
display_rotate=3
```

### 5. Screen Goes Black (Power Saving)

**Symptoms:**
- Screen turns off after a few minutes
- Kiosk becomes unusable

**Solution:**
```bash
# Disable screen blanking
sudo nano /etc/lightdm/lightdm.conf

# Add under [Seat:*]:
xserver-command=X -s 0 -dpms

# Alternative: Edit ~/.xsessionrc
echo "xset s off" >> ~/.xsessionrc
echo "xset -dpms" >> ~/.xsessionrc
```

### 6. Kiosk UI Too Small/Large

**Symptoms:**
- Buttons and text are too small for touch use
- UI elements are too large and get cut off

**Solution:**
The kiosk automatically adjusts for 1024x600, but you can manually adjust:

Edit `kiosk_browser.py` around line 65:
```python
# For smaller UI elements
self.setGeometry(0, 0, 1024, 600)

# For larger touch targets, app will auto-scale
```

### 7. Performance Issues

**Symptoms:**
- Slow scrolling or page loading
- Jerky animations

**Solution:**
```bash
# Increase GPU memory
sudo nano /boot/config.txt
# Add: gpu_mem=64

# Use hardware acceleration
cd /home/pi/office_kiosk
./fix_pi_graphics.sh

sudo reboot
```

## Verification Commands

### Check Display Resolution
```bash
xrandr | grep "*"
```

### Check Touch Devices
```bash
xinput list
```

### Test Touch Input
```bash
evtest /dev/input/event0
# Replace event0 with your touch device
```

### Check GPU Memory
```bash
vcgencmd get_mem gpu
```

### View Boot Configuration
```bash
cat /boot/config.txt | grep -E "(hdmi|display)"
```

## Quick Reset

If everything goes wrong, reset display config:
```bash
cd /home/pi/office_kiosk
sudo cp /boot/config.txt.backup.* /boot/config.txt
sudo ./setup_waveshare.sh
sudo reboot
```

## Getting Help

1. **Run diagnostics**: `./debug_startup.sh`
2. **Check hardware**: Verify power supply (5V 3A minimum)
3. **Test cables**: Ensure HDMI and USB connections are secure
4. **Update firmware**: `sudo rpi-update`
5. **Check logs**: `dmesg | grep -i touch`

#!/usr/bin/python3

import cv2
import imutils # Installed with PIP
import numpy
import subprocess
import secrets

# Using /dev/shm to reduce writes to the SD card
IMAGE_PATH = "/dev/shm/renogy_lcd.bmp"
ON_THRESHOLD = 50
ROT_ANGLE = 177
BOX_SIZE = 5


# For now I am manually finding the pixel coordinates from the bmp and entering them here. If I
# find that I am having to go in and adjust these frequenly I plan to make it smarter.
AC_POWER = (1107, 1281)

DIGIT_HEIGHT = 130
DIGIT_WIDTH = 68
# Point at top right of digit
IN_HUNDRED = (1130, 956)
IN_TEN = (1230, 956)
IN_ONE = (1331, 956)
OUT_HUNDRED = (1849, 954)
OUT_TEN = (1950, 954)
OUT_ONE = (2052, 954)

CAP_25 = (1548, 1450)
# Capacity line seperation
CAP_SPACE = 21
CAP_50 = (CAP_25[0], CAP_25[1] - CAP_SPACE)
CAP_75 = (CAP_25[0], CAP_50[1] - CAP_SPACE)
CAP_100 = (CAP_25[0], CAP_75[1] - CAP_SPACE)


class Number:
    segPos = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6}

    def __init__(self):
        self.hundred = [False, False, False, False, False, False, False]
        self.ten = [False, False, False, False, False, False, False]
        self.one = [False, False, False, False, False, False, False]

    def segNumber(self, digit):
        if digit == [True, True, True, True, True, True, False] or \
                digit == [False, False, False, False, False, False, False]:
            return 0
        elif digit == [False, True, True, False, False, False, False]:
            return 1
        elif digit == [True, True, False, True, True, False, True]:
            return 2
        elif digit == [True, True, True, True, False, False, True]:
            return 3
        elif digit == [False, True, True, False, False, True, True]:
            return 4
        elif digit == [True, False, True, True, False, True, True]:
            return 5
        elif digit == [True, False, True, True, True, True, True]:
            return 6
        elif digit == [True, True, True, False, False, False, False]:
            return 7
        elif digit == [True, True, True, True, True, True, True]:
            return 8
        elif digit == [True, True, True, True, False, True, True]:
            return 9

    def result(self):
        return 100 * self.segNumber(self.hundred) + 10 * self.segNumber(self.ten) + self.segNumber(self.one)

    def setSeg(self, place, pos, val):
        if place == "hundred":
            self.hundred[self.segPos[pos]] = val
        if place == "ten":
            self.ten[self.segPos[pos]] = val
        if place == "one":
            self.one[self.segPos[pos]] = val


def intersectToCoords(sqList, tag, place, coord):
    x = coord[0]
    y = coord[1]

    sqList.append([(x - int(DIGIT_WIDTH/2), y), BOX_SIZE, tag, place, 'a'])
    sqList.append([(x, y + int(DIGIT_HEIGHT/4)), BOX_SIZE, tag, place, 'b'])
    sqList.append([(x, y + int(DIGIT_HEIGHT/4*3)), BOX_SIZE, tag, place, 'c'])
    sqList.append([(x - int(DIGIT_WIDTH/2), y + DIGIT_HEIGHT), BOX_SIZE, tag, place, 'd'])
    sqList.append([(x - DIGIT_WIDTH, y + int(DIGIT_HEIGHT/4*3)), BOX_SIZE, tag, place, 'e'])
    sqList.append([(x - DIGIT_WIDTH, y + int(DIGIT_HEIGHT/4)), BOX_SIZE, tag, place, 'f'])
    sqList.append([(x - int(DIGIT_WIDTH/2), y + int(DIGIT_HEIGHT/2)), BOX_SIZE, tag, place, 'g'])


inputV = Number()
outputV = Number()
acPower = False
capacity = 0

# Add coordinates to list
monitorSquares = []
intersectToCoords(monitorSquares, "inputV", "hundred", IN_HUNDRED)
intersectToCoords(monitorSquares, "inputV", "ten", IN_TEN)
intersectToCoords(monitorSquares, "inputV", "one", IN_ONE)
intersectToCoords(monitorSquares, "outputV", "hundred", OUT_HUNDRED)
intersectToCoords(monitorSquares, "outputV", "ten", OUT_TEN)
intersectToCoords(monitorSquares, "outputV", "one", OUT_ONE)

monitorSquares.append([AC_POWER, BOX_SIZE, "acPower"])
monitorSquares.append([CAP_25, BOX_SIZE, "cap25Percent"])
monitorSquares.append([CAP_50, BOX_SIZE, "cap50Percent"])
monitorSquares.append([CAP_75, BOX_SIZE, "cap75Persent"])
monitorSquares.append([CAP_100, BOX_SIZE, "cap100Percent"])


while True:
    print("Capturing LCD", flush=True)
    subprocess.run(["/usr/bin/libcamera-still", "-n", "-e", "bmp", "-o", IMAGE_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Importing Image", flush=True)
    renoDisp = cv2.cvtColor(imutils.rotate_bound(cv2.imread(IMAGE_PATH), ROT_ANGLE), cv2.COLOR_BGR2GRAY)

    print("Analyzing", flush=True)
    for sq in monitorSquares:
        val = numpy.average(renoDisp[sq[0][1] - BOX_SIZE:sq[0][1] + BOX_SIZE, sq[0][0] - BOX_SIZE:sq[0][0] + BOX_SIZE])
        cv2.rectangle(renoDisp, (sq[0][0] - BOX_SIZE, sq[0][1] - BOX_SIZE), (sq[0][0] + BOX_SIZE, sq[0][1] + BOX_SIZE), (255), 1)
        
        if val > ON_THRESHOLD:
            bolVal = True
        else:
            bolVal = False

        tag = sq[2]
        if tag == "inputV":
            inputV.setSeg(sq[3], sq[4], bolVal)
            continue

        if tag == "outputV":
            outputV.setSeg(sq[3], sq[4], bolVal)
            continue

        if tag == "acPower":
            acPower = bolVal
            continue
            
        if tag == "cap25Percent":
            if bolVal and capacity < 25:
                capacity = 25
            continue

        if tag == "cap50Percent":
            if bolVal and capacity < 50:
                capacity = 50
            continue

        if tag == "cap75Persent":
            if bolVal and capacity < 75:
                capacity = 75
            continue

        if tag == "cap100Percent":
            if bolVal and capacity < 100:
                capacity = 100
            continue

    print("Exporting Image", flush=True)
    cv2.imwrite("{}_mod.bmp".format(IMAGE_PATH), renoDisp)
    
    print("In Volt: {}, Out Volt: {}, Capacity: {}, AC Power: {}".format(inputV.result(), outputV.result(), capacity, acPower), flush=True)

    if not acPower and capacity <= 25:
        ups_status = "OB LB"
    elif not acPower:
        ups_status = "OB"
    else:
        ups_status = "OL"

    subprocess.run(["/usr/local/ups/bin/upsrw", "-w", "-u", "updater", "-p", secrets.nut_pw, "-s", "input.voltage={}".format(inputV.result()), "renogy"])
    subprocess.run(["/usr/local/ups/bin/upsrw", "-w", "-u", "updater", "-p", secrets.nut_pw, "-s", "output.voltage={}".format(outputV.result()), "renogy"])
    subprocess.run(["/usr/local/ups/bin/upsrw", "-w", "-u", "updater", "-p", secrets.nut_pw, "-s", "battery.charge={}".format(capacity), "renogy"])
    subprocess.run(["/usr/local/ups/bin/upsrw", "-w", "-u", "updater", "-p", secrets.nut_pw, "-s", "ups.status={}".format(ups_status), "renogy"])

    # Init variables
    capacity = 0

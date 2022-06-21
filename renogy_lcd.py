#!/usr/bin/python3

import cv2
import imutils # Installed with PIP
import numpy
import subprocess
import secrets

# Using /dev/shm to reduce writes to the SD card
IMAGE_PATH = "/dev/shm/renogy_lcd.bmp"
REF_PATH = "/home/pi/renogy/bulb.bmp"
ON_THRESHOLD = 50
ROT_ANGLE = 177
BOX_SIZE = 5

# Coordinates are relative to a point that is at the top left of the bulb
# reference image
AC_POWER = (786, -17)

DIGIT_HEIGHT = 130
DIGIT_WIDTH = 68
# Point at top right of digit
IN_HUNDRED = (763, 312)
IN_TEN = (663, 312)
IN_ONE = (562, 312)
OUT_HUNDRED = (44, 315)
OUT_TEN = (-57, 315)
OUT_ONE = (-159, 315)

CAP_25 = (345, -181)
# Capacity line seperation
CAP_SPACE = 21
CAP_50 = (CAP_25[0], CAP_25[1] + CAP_SPACE)
CAP_75 = (CAP_25[0], CAP_50[1] + CAP_SPACE)
CAP_100 = (CAP_25[0], CAP_75[1] + CAP_SPACE)

LOAD_25 = (-147, -160)
LOAD_SPACE = 44
LOAD_50 = (LOAD_25[0], LOAD_25[1] + LOAD_SPACE)
LOAD_75 = (LOAD_25[0], LOAD_50[1] + LOAD_SPACE)
LOAD_100 = (LOAD_25[0], LOAD_75[1] + LOAD_SPACE)


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

        raise Exception("Not a valid sequence of segment values")

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

    sqList.append([(x + int(DIGIT_WIDTH/2), y), BOX_SIZE, tag, place, 'a'])
    sqList.append([(x, y - int(DIGIT_HEIGHT/4)), BOX_SIZE, tag, place, 'b'])
    sqList.append([(x, y - int(DIGIT_HEIGHT/4*3)), BOX_SIZE, tag, place, 'c'])
    sqList.append([(x + int(DIGIT_WIDTH/2), y - DIGIT_HEIGHT), BOX_SIZE, tag, place, 'd'])
    sqList.append([(x + DIGIT_WIDTH, y - int(DIGIT_HEIGHT/4*3)), BOX_SIZE, tag, place, 'e'])
    sqList.append([(x + DIGIT_WIDTH, y - int(DIGIT_HEIGHT/4)), BOX_SIZE, tag, place, 'f'])
    sqList.append([(x + int(DIGIT_WIDTH/2), y - int(DIGIT_HEIGHT/2)), BOX_SIZE, tag, place, 'g'])


inputV = Number()
outputV = Number()
acPower = False
capacity = 0
load = 0

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

monitorSquares.append([LOAD_25, BOX_SIZE, "load25percent"])
monitorSquares.append([LOAD_50, BOX_SIZE, "load50percent"])
monitorSquares.append([LOAD_75, BOX_SIZE, "load75percent"])
monitorSquares.append([LOAD_100, BOX_SIZE, "load100percent"])

# Load reference point
bulb = cv2.cvtColor(cv2.imread(REF_PATH), cv2.COLOR_BGR2GRAY)

while True:
    print("Capturing LCD", flush=True)
    subprocess.run(["/usr/bin/libcamera-still", "-n", "-e", "bmp", "-o", IMAGE_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Importing Image", flush=True)
    renoDisp = cv2.cvtColor(imutils.rotate_bound(cv2.imread(IMAGE_PATH), ROT_ANGLE), cv2.COLOR_BGR2GRAY)
    
    print("Finding Bulb", flush=True)
    bulb_coord = cv2.minMaxLoc(cv2.matchTemplate(bulb, renoDisp, cv2.TM_SQDIFF_NORMED))[2]
    cv2.circle(renoDisp, bulb_coord, 4, (255), -1)

    print("Bulb: {}".format(bulb_coord))

    print("Analyzing", flush=True)
    for sq in monitorSquares:
        center_pt = (bulb_coord[0] - sq[0][0], bulb_coord[1] - sq[0][1])
        # print("{}, {}".format(center_pt, sq))

        val = numpy.average(renoDisp[center_pt[1] - BOX_SIZE:center_pt[1] + BOX_SIZE, center_pt[0] - BOX_SIZE:center_pt[0] + BOX_SIZE])
        cv2.rectangle(renoDisp, (center_pt[0] - BOX_SIZE, center_pt[1] - BOX_SIZE), (center_pt[0] + BOX_SIZE, center_pt[1] + BOX_SIZE), (255), 1)
        
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

        if tag == "load25percent":
            if bolVal and load < 25:
                load = 25
            continue

        if tag == "load50percent":
            if bolVal and load < 50:
                load = 50
            continue

        if tag == "load75percent":
            if bolVal and load < 75:
                load = 75
            continue

        if tag == "load100percent":
            if bolVal and load < 100:
                load = 100
            continue

    print("Exporting Image", flush=True)
    cv2.imwrite("{}_mod.bmp".format(IMAGE_PATH), renoDisp)

    if not acPower and capacity <= 25:
        ups_status = "OB LB"
    elif not acPower:
        ups_status = "OB"
    else:
        ups_status = "OL"

    # Sometimes the exposure will overlap a lcd update and the results from reading the 7 segment digits will not produce
    # a numeric output.
    try:
        inputVolts = inputV.result()
        outputVolts = outputV.result()
    except Exception as error:
        print("ERROR: {}}".format(error))
    else:
        print("In Volt: {}, Out Volt: {}, Capacity: {}, Load: {}, AC Power: {}".format(inputVolts, outputVolts, capacity, load, acPower), flush=True)

        subprocess.run(["/usr/local/ups/bin/upsrw", "-w", "-u", "renogy_lcd", "-p", secrets.nut_pw, "-s", "input.voltage={}".format(inputVolts), "renogy"])
        subprocess.run(["/usr/local/ups/bin/upsrw", "-w", "-u", "renogy_lcd", "-p", secrets.nut_pw, "-s", "output.voltage={}".format(outputVolts), "renogy"])
        subprocess.run(["/usr/local/ups/bin/upsrw", "-w", "-u", "renogy_lcd", "-p", secrets.nut_pw, "-s", "battery.charge={}".format(capacity), "renogy"])
        subprocess.run(["/usr/local/ups/bin/upsrw", "-w", "-u", "renogy_lcd", "-p", secrets.nut_pw, "-s", "ups.status={}".format(ups_status), "renogy"])
        subprocess.run(["/usr/local/ups/bin/upsrw", "-w", "-u", "renogy_lcd", "-p", secrets.nut_pw, "-s", "ups.load={}".format(load), "renogy"])

    # Init variables
    capacity = 0
    load = 0

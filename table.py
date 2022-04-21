import math
import matplotlib.pyplot as plt
import discord
import os
import random
from matplotlib.cbook import get_sample_data
import globals
import datetime

# players
players = []
playerCount = 0

# plot
font = {'family': 'serif',
        'size': 14}
plt.rc('font', **font)
nameRad = 0.72
circRad = 0.6
xCoords = []
yCoords = []
hAlignments = []
vAlignments = []

# clock image
clock = 'clock1.jpg'
clockPicsPath = os.getcwd() + '/clockpics'
clockPicNames = os.listdir(clockPicsPath)
random.shuffle(clockPicNames)
imRad = 0.8 * circRad

# misc
mostRecentPostTime = datetime.datetime.now()


def table_setup(playerList):
    global players, playerCount, xCoords, yCoords, hAlignments, vAlignments
    players = playerList
    playerCount = len(players)
    degreeStep = -2 * math.pi / playerCount
    degreePoints = []
    degreePoints.extend(range(playerCount))
    degreePoints = [x * degreeStep + degreeStep / 2 for x in degreePoints]

    for pt in degreePoints:
        x = nameRad * math.cos(pt)
        y = nameRad * math.sin(pt)
        if x > 0.3 * circRad:
            hAlignments.append('left')
        elif x < -0.3 * circRad:
            hAlignments.append('right')
        else:
            hAlignments.append('center')
        if y > 0.3 * circRad:
            vAlignments.append('bottom')
        elif y < -0.3 * circRad:
            vAlignments.append('top')
        else:
            vAlignments.append('center')
        xCoords.append(x)
        yCoords.append(y)


def draw_table(new_picture=None):
    global clockPicNames, mostRecentPostTime, clock
    # mostRecentPostTime = datetime.datetime.now()

    fig, ax = plt.subplots()
    ax.set_aspect(1)
    plt.axis([-nameRad, nameRad, -nameRad, nameRad])
    circ = plt.Circle((0, 0), circRad, color='saddlebrown', lw=1.5, fill=False)
    ax.add_patch(circ)
    plt.axis('off')

    for i in range(playerCount):
        clr = 'black'
        label = players[i].nickname + '\n(' + players[i].alias + ')'
        if not players[i].alive:
            label = strikethrough(label)
            clr = 'r'
        plt.text(xCoords[i], yCoords[i], label, ha=hAlignments[i], va=vAlignments[i], color=clr)

    if new_picture is not None:
        try:
            clock = clockPicNames.pop()
        except IndexError:
            clock = 'clock1.jpg'

    im = plt.imread(get_sample_data(clockPicsPath + '/' + clock))
    plt.imshow(im, extent=[-imRad, imRad, -imRad, imRad])

    plt.savefig('table.png')


async def show_table(channels):
    for channel in channels:
        await channel.send(file=discord.File('table.png'))


def strikethrough(text):
    result = ''
    for c in text:
        if c != '\n':
            result = result + c + '\u0336'
        else:
            result = result + c
    return result




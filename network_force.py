"""
Week 6

Ray Hu & Xietao
"""

import numpy as np
import matplotlib.pyplot as plt
import random

"""
Parameters.
numberOfRods: the number of rods, also the number of motors.
length: the length of the rods, enter a matrix of size equal to the number of rods.
velocity_d: diffusion velocity.
velocity_p: persistence velocity.
seed: seed used to generate motor position.
makeAnimation: set True if you want simulation animated, set False to skip.
repeatedSystems: set True for multiple simulations with different seed.
numberOfRepetitions: if repeatedSystems is True, then set here the number of desired simualations.
seqUpdate: 0 for top to bottom, 1 for bottom to top, 
2 is (uniformly) self-avoiding random, 3 for (uniformly) completely random. Default is 0.
diffSampling: 0 is constant, 1 for uniformly distribution, 2 Gaussian.
persSample: 0 is constant, 1 for uniformly distribution, 2 Gaussian.
allowMotorCrossing: set True to allow motor crossing.
finalTime: number of timesteps to be considered.
recordTime: number of timesteps before each recording.
motors: motors initial condition w.r.t the rods, enter the full matrix.
"""

numberOfRods = 2001
length = np.ones(numberOfRods)
velocity_d = 0.0001
velocity_p = 0.01
seed = 1
makeAnimation = False
repeatedSystems = False
numberOfRepetitions = 2000
# Don't change these
np.random.seed(seed)
random.seed(seed)
# ----
seqUpdate = 2
diffSampling = 2
persSample = 0
allowMotorCrossing = True
finalTime = 800
recordTime = 2
motors = np.random.rand(numberOfRods, 2)

def RodsArray(Rposition, Mposition, length, numberOfRods):

    for i in range(1, numberOfRods):
        Rposition[i, 0] += Rposition[i-1, 0] + Mposition[i-1, 0] - Mposition[i-1, 1]

    Rposition[:, 1] = length #Array
    
    return Rposition

def randwalk(numberofsteps, Rposition, Mposition, numberOfRods, pervF, diffuF):
    # randomwalk with velocity v_d and directional movement with v_p 
    F_p = 1
    F_d = 1
    v1 = np.zeros(numberOfRods)
    v2 = np.zeros(numberOfRods)
    for k in range(1, numberofsteps): 
        Ran = list(range(0, -numberOfRods, -1))
        random.shuffle(Ran)
        for i in Ran: #for each rod
            dice1 = np.random.uniform(-1,1)
            v1[i] += F_p + dice1 * F_d #Add force in this structure
            Mposition[i, 0] += v1[i]
            if (0 >= Mposition[i, 0] or  Mposition[i, 0] >= Rposition[i, 1] ):
                Mposition[i, 0] -= v1[i]
            else:
                pass
            
            dice2 = np.random.uniform(-1,1)
            v2[i] += - F_p + dice2 * F_p 
            Mposition[i, 1] += v2[i]
            if (0 >= Mposition[i, 1] or  Mposition[i, 1] >= Rposition[i, 1] ):
                Mposition[i, 1] -= v2[i]
            else:
                pass
        Rposition[1:, 0] = (Mposition[:-1, 0] - Mposition[:-1, 1]).cumsum()
    
    return Rposition, Mposition

def calculateMotorPositions(RodsMatrix, MotorMatrix, numberOfMotors):

    motorPositions = np.zeros(numberOfMotors)
    position = RodsMatrix[0, 0] + MotorMatrix[0, 0]
    motorPositions[0] = position
    for motor in range(1, numberOfMotors):
        position = (RodsMatrix[motor, 0] + MotorMatrix[motor, 0])
        motorPositions[motor] = position
    
    return motorPositions

def systemLength(RodsMatrix, numberOfMotors):

    rightMostPositions = np.zeros(numberOfMotors)
    for rod in range(0, numberOfMotors):
        rightMostPositions[rod] = RodsMatrix[rod, 0] + RodsMatrix[rod, 1]
    length = -np.amin(RodsMatrix[:, 0]) + np.amax(rightMostPositions)
    return length

def multipleSimulations(numberOfSimulations, length, numberOfRods, finalTime, recordTime, plotEvol):
    
    finalLength = np.zeros(numberOfSimulations)
    allLengths = np.zeros((numberOfSimulations, int(finalTime/recordTime)))
    seeds = [None]*numberOfSimulations
    for simul, seed in enumerate(np.random.choice(1000000, numberOfSimulations, replace=False)):
        seeds[simul] = np.random.default_rng(seed=seed)
    
    for simul in range(0, numberOfSimulations):
        rods = np.zeros((numberOfRods, 2))
        motors = seeds[simul].random((numberOfRods, 2))
        rods = RodsArray(rods, motors, length, numberOfRods)

        for tstep in range(0, int(finalTime/recordTime)):
            rods, motors = randwalk(recordTime, rods, motors, numberOfRods, velocity_p, velocity_d)
            lengthArray[tstep] = systemLength(rods, numberOfRods)
        if plotEvol:
            plt.scatter(np.linspace(0, lengthArray.size, lengthArray.size), lengthArray)
            plt.title('Rod length evolution')
            plt.xlabel('Time step')
            plt.ylabel('Rod length')
        if simul % 100 == 0:
            print(f'Currently {simul}/{numberOfSimulations}')

        finalLength[simul] = lengthArray[-1]
        allLengths[simul] = lengthArray

    return finalLength, allLengths

def plotSystem(RodsMatrix, MotorsMatrix, numberOfRods, gridPoints):

    motorPos = calculateMotorPositions(RodsMatrix, MotorsMatrix, numberOfRods)
    plt.clf()
    for row in range(0, numberOfRods):
        'Rods'
        y_r = np.ones(gridPoints)*row*0.2
        x_r = np.linspace(RodsMatrix[row, 0], RodsMatrix[row, 0] + RodsMatrix[row, 1], gridPoints, endpoint=True)
        
        plt.plot(x_r, y_r)
        'Motors'
        y_m = row*0.2 + 0.1
        x_m = motorPos[row]
        plt.scatter(x_m, y_m)

    plt.xlabel('x coordinate, motors in dots')
    plt.ylabel('Rods, rod 1 is y = 0, next rod is y += 0.2')
    plt.title('1D System')
    plt.pause(0.1)

def plotLengthEvolution(lengths):

    plt.plot(np.linspace(0, lengths.size, lengths.size), lengths)
    plt.title('Rod length evolution')
    plt.xlabel('Time step')
    plt.ylabel('Rod length')
    #plt.show()

rods = np.zeros((numberOfRods, 2))
rods = RodsArray(rods, motors, length, numberOfRods)
lengthArray = np.zeros(int(finalTime/recordTime))

for tstep in range(0, int(finalTime/recordTime)):

    rods, motors = randwalk(recordTime, rods, motors, numberOfRods, velocity_p, velocity_d)
    lengthArray[tstep] = systemLength(rods, numberOfRods)
    if makeAnimation == True:
        plotSystem(rods, motors, numberOfRods, 10)

plt.show()
plotLengthEvolution(lengthArray)
if repeatedSystems == True:
    lengthFinal, lengths = multipleSimulations(numberOfRepetitions, length, numberOfRods, finalTime, recordTime, False)
plt.show()

# Save to files, use graphs jupyter notebook to plot these
np.savetxt('rods.dat', rods)
np.savetxt('motors.dat', motors)
if repeatedSystems == True:
    np.savetxt('length_final.dat', lengthFinal)
    np.savetxt('length_all.dat', lengths)
import numpy as np
import random
import matplotlib.pyplot as plt
import time
import os
import json

"""
Term 2 Week 3

Authors: Ray & Xietao

Parameters.
n_cols: number of columns in the lattice.
n_rows: number of rows in the lattice.
length: length of the rods.
velocity_d: diffusion velocity. (in nm/ns)
velocity_p: persistence velocity. (in nm/ns)
seed: seed used to generate motor position.
makeAnimation: set True if you want simulation animated, set False to skip.
finalTime: number of timesteps to be considered. (in ns)
recordTime: number of timesteps before each recording. (in ns)
motor_scale: initial position of the motors in each rod (in nm)
threshold: insert here a number from (0, 1) for reduced connectivity.
ratio: mass of rod/mass of motor
"""

n_cols = 15
n_rows = 15
length = 1000
velocity_d = 10
velocity_p = 1
seed = 1
makeAnimation = False
finalTime = 1000
recordTime = 1
motor_scale = 350
threshold = -1
ratio = 3
relatives = False

# Format parameters
parameters = {
    "n_cols": n_cols,
    "n_rows": n_rows,
    "length": length,
    "vp": velocity_p,
    "vd": velocity_d,
    "seed": seed,
    "finalTime": finalTime,
    "recordTime": recordTime,
    "motor_scale": motor_scale,
    "threshold": threshold
}

# Folder to save results. Set to 0 for same workspace.
folder_path = 0

# Obtain current time to automatically save different results
unix_time = time.time()
print(f'Current time: {unix_time}')

# Initialise seeds
np.random.seed(seed)
random.seed(seed)

class Rod:
    def __init__(self, length, polarisation, pluspos, motor1, motor2):
        self.length = length
        self.polarisation = np.array(polarisation,dtype='float64')
        self.pluspos = np.array(pluspos ,dtype='float64')
        self.minuspos = np.array(self.pluspos) + np.array(self.polarisation) * self.length
        self.motor1 = motor1
        self.motor2 = motor2
        self.pos1 = motor1.get_position()
        self.pos2 = motor2.get_position()

    def get_polarisation(self):
        return self.polarisation
    
    def get_pluspos(self):
        return self.pluspos
    
    #The self polarisation is pointing from plus to minus
    def get_minuspos(self):
        return self.minuspos
    
    def get_vector(self):
        return self.polarisation * self.length
    
    def within_bounds(self):
        """Check if a position is within the bounds of the rod"""
        # check the distance between pos and pos1 and pos and pos2 
        return np.linalg.norm(self.pluspos - self.pos1) <= self.length and np.linalg.norm(self.pluspos - self.pos2) <= self.length and np.linalg.norm(self.minuspos - self.pos1) <= self.length and np.linalg.norm(self.minuspos - self.pos2) <= self.length
    
    def in_line_with_rod(self, pos, polarisation):
        """Check if a position is in line with the rod"""
        # check if pos = pos1 + lambda * polarisation
        lambda_value = np.dot((pos - self.pluspos), polarisation) 
        return np.allclose(pos, self.pluspos + lambda_value * self.polarisation)

    def reconnect(self, fixed_motor):
        """Reconnect a moved motor to the rod if it has moved outside of the rod"""
        if fixed_motor == self.motor1:
            moved_motor = self.motor2
            moved_motor_pos = self.motor2.get_position()
            fixed_motor_pos = self.motor1.get_position()
        else:
            moved_motor = self.motor1
            moved_motor_pos = self.motor1.get_position()
            fixed_motor_pos = self.motor2.get_position()
        fixed_motor_distance = np.linalg.norm(fixed_motor.get_position() - self.pluspos)
        moved_motor_distance = np.linalg.norm(moved_motor.get_position() - self.pluspos)
        #print('inline', self.in_line_with_rod(moved_motor_pos, self.polarisation))
        if not self.within_bounds():
            return self
        elif not self.in_line_with_rod(moved_motor_pos, self.polarisation):
            #print('elif', fixed_motor_distance < moved_motor_distance)
            if fixed_motor_distance < moved_motor_distance:
                movable_length = self.length - fixed_motor_distance
                self.polarisation = moved_motor_pos - fixed_motor_pos
                self.polarisation = self.polarisation / np.linalg.norm(self.polarisation)
                #self.length = np.linalg.norm(moved_motor_pos - fixed_motor_pos)
                self.pluspos = fixed_motor_pos - (self.polarisation * fixed_motor_distance)
                self.minuspos = np.array(self.pluspos) + np.array(self.polarisation) * self.length
        
        
            else:
                movable_length = fixed_motor_distance
                self.polarisation = -moved_motor_pos + fixed_motor_pos
                self.polarisation = self.polarisation / np.linalg.norm(self.polarisation)
                #self.length = np.linalg.norm(fixed_motor_pos - moved_motor_pos)
                self.pluspos = fixed_motor_pos - (self.polarisation * movable_length)
                self.minuspos = np.array(self.pluspos) + np.array(self.polarisation) * self.length
        return self


class Motor:
    def __init__(self, pos, v_p, v_D):
        self.position = np.array(pos,dtype='float64')
        self.v_p = v_p
        self.v_d = v_D
        self.connected_rods = []
        
    def add_rod(self, rod):
        self.connected_rods.append(rod)
        
    def move(self):
        # Pick a random rod to move along
        #print(len(self.connected_rods))
        rod = random.choice(self.connected_rods)
        polarisation = rod.get_polarisation()
        movement = (self.v_p + self.v_d * random.uniform(-1,1)) * polarisation
        #print(type(movement))
        self.position += movement
        # Check if motor goes out of the rod
        out_of_bounds = False
        for rod in self.connected_rods:
            if not rod.within_bounds():
                out_of_bounds = True
        if out_of_bounds:
            self.position -= movement
    def get_position(self):
        return self.position
    
    def get_v_p(self):
        return self.v_p
    
    def get_v_d(self):
        return self.v_d
    
    def get_relative_pos(self):
        relative_pos = np.zeros(len(self.connected_rods))
        for i, rod in enumerate(self.connected_rods):
            relative_pos[i] = np.linalg.norm(rod.pluspos - self.position)
        return relative_pos

def generate_lattice_network(n, m, rod_length):
    rods = dict()
    motors = dict()
    for i in range(n):
        for j in range(m):
            if i<n+1 and j<m+1:
                motors[(i*m)+j] = Motor(np.multiply((i, j), motor_scale), velocity_p, velocity_d)
    for i in range(n):
        for j in range(m):
            if  i < n - 1 and np.random.random() > threshold:
                rods[((i*m)+j, (i*m + m)+j)] = Rod(rod_length, (1,0), np.multiply((i,j), motor_scale), motors[(i*m)+j], motors[(i*m + m)+j])
            if  j < m - 1 and np.random.random() > threshold:
                rods[((i*m)+j, (i*m)+j + 1)] = Rod(rod_length, (0,1), np.multiply((i,j), motor_scale), motors[(i*m)+j ], motors[((i*m)+j) + 1])
            
    return rods, motors

def movement(rods,motors, n, m):
    Rann = list(range(n))
    random.shuffle(Rann)
    Ranm = list(range(m))
    random.shuffle(Ranm)
    #print(Rann)
    
    for i in Rann:
        for j in Ranm:
            motor = motors[i*m + j]
            if ((i*m)+j) < (n*m) and ((i*m + m)+j) < (n*m) and ((i*m)+j, (i*m + m)+j) in rods:
                rod1 = rods[(i*m)+j,(i*m + m)+j]
                motor.add_rod(rod1)
            if ((i*m - m)+j) >= 0 and ((i*m)+j) < (n*m) and ((i*m - m)+j, (i*m)+j) in rods:
                rod2 = rods[(i*m - m)+j,(i*m)+j]
                motor.add_rod(rod2)
            if ((i*m)+j) < (n*m) and ((i*m)+j + 1) < (n*m) and ((i*m)+j, (i*m)+j + 1) in rods:
                rod3 = rods[(i*m)+j,(i*m)+j + 1]
                motor.add_rod(rod3)
            if ((i*m)+j - 1) >= 0 and ((i*m)+j) < (n*m) and ((i*m)+j - 1, (i*m)+j) in rods:
                rod4 = rods[(i*m)+j - 1,(i*m)+j]
                motor.add_rod(rod4)
            motor.move()
            for rod in motor.connected_rods:
                if rod in rods.values():
                    rod.reconnect(motor)


    return rods, motors     
            
def simulate(rods,motors, n, m, timesteps):
    for timestep in range(timesteps):
        movement(rods, motors, n, m)
        if relatives and not timestep == timesteps-1:
            for motor in range(n*m):
                motors[motor].connected_rods = []
        else:
            for motor in range(n*m):
                motors[motor].connected_rods = []
        
    return rods, motors

def drawArrow(A, B):
    plt.arrow(A[0], A[1], B[0] - A[0], B[1] - A[1], head_width=30, length_includes_head=True)

def center_of_mass(rods, motors, ratio):
    com = np.zeros(2)
    total_mass = (len(motors.values())+ ratio * len(rods.values()))
    for rod in rods.values():
        com += ratio * 0.5 *(rod.get_pluspos() + rod.get_minuspos())/total_mass
    for motor in motors.values():
        com += motor.get_position()/total_mass  
    return com

# Create folder for saving data.
if folder_path == 0:
    folder_path = os.getcwd()
folder = os.path.join(folder_path, str(unix_time))
os.mkdir(folder)

# Dump parameters
with open(f'{folder}\\parameters.json', 'w') as fp:
    json.dump(parameters, fp)

rods, motors = generate_lattice_network(n_cols, n_rows, length)
com_over_time = np.zeros((finalTime, 2))
start_time = time.time()
for timestep in range(finalTime):
    if timestep % 100 == 0:
        print(f'Current step: {timestep}/{finalTime}')
    rods, motors = simulate(rods, motors, n_cols, n_rows, recordTime)
    com_over_time[timestep] = center_of_mass(rods, motors, ratio)
    if not makeAnimation:
        continue
    
    # Draw the rods
    for rod in rods.values():
        drawArrow(rod.get_pluspos(), rod.get_minuspos())

    # Draw the motors
    for motor in motors.values():
        plt.scatter(motor.get_position()[0], motor.get_position()[1])  
    plt.scatter(0, 0, label=timestep, marker='x')
    plt.legend()
    plt.pause(0.1)
    plt.clf()
end_time = time.time()
elapsed_time = end_time - start_time
print(f'Time elapsed: {elapsed_time} seconds.')

plt.show()

plt.plot(np.linspace(0, finalTime, finalTime), com_over_time)
plt.show()

# Save CoM over time
np.savetxt('com.dat', com_over_time)
np.savetxt(f'{folder}\\com-{unix_time}.dat', com_over_time)

# Save final positions of motors.
motors_pos = np.ones((len(list(motors.values())), 2))
for i, motor in enumerate(list(motors.values())):
    motors_pos[i] = motor.position
np.savetxt('motors.dat', motors_pos)
np.savetxt(f'{folder}\\motors-{unix_time}.dat', motors_pos)

# This is a simulation for ONLY relative positions.
if relatives:
    rods, motors = generate_lattice_network(n_cols, n_rows, length)
    relatives = np.array([])
    simulate(rods, motors, n_cols, n_rows, 4000)
    for i, motor in enumerate(list(motors.values())):
        relatives = np.hstack((relatives, motor.get_relative_pos()))
    np.savetxt('relatives.dat', relatives)
    np.savetxt(f'{folder}\\relatives-{unix_time}.dat', relatives)
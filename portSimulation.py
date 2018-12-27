#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 20 18:43:41 2018

@author: 
"""

"""
Title: Port Simulation

Scenario:

TODO

"""
import itertools
import random

import simpy
import numpy as np

RANDOM_SEED = 42

SIM_TIME = 100              # Simulation time in seconds
# 1 second in the simulation equates to 1 hour in the real world scenario

# 3 equal docks
DOCKS = 3

# 1 tug
TUGS = 1

UNLOAD_SPEED = 1

# average traveling time for ships of type 1 to 3
AVG_TRAVEL_TYPE1_3 = 11

# average unloading time for ships of type 1
UNLOAD_TIME_TYPE_1 = [16, 20]

# average unloading time for ships of type 2
UNLOAD_TIME_TYPE_2 = [21, 25]

# average unloading time for ships of type 3
UNLOAD_TIME_TYPE_3 = [32, 40]

"""----- Ship distribution by type ----"""
# ship distribution of ships type 1 to 3 {type 1: 25%, type 2: 55%, type 3: 20%}
SHIP_DISTR = [1,1,1,1,1,2,2,2,2,2,2,2,2,2,2,2,3,3,3,3]

"""----- Ship Type 4 ; 5 ships -----"""
#type_4_ships = 5
SHIPS_TYPE_4 = 5
# average traveling time for ships of type 4
AVG_TRAVEL_TYPE4 = 240
# average unloading time for ships of type 4
UNLOAD_TIME_TYPE_4 = [18, 24]

# tug service is busy for 1 hour for one direction
TUG_TIME_ONE_WAY = 1

"""-----------LOG----------------"""
port_waiting_time = []
load_sum = []

def ship_generator_type_4(env, tug, dock, ships_type_4):
    while True:
        env.process(ship('Ship_Type_4 %d' % ships_type_4.level, env, tug, dock, 4))
        yield ships_type_4.get(1)

def ship_generator(env, tug, dock):
    #Generate new ships.
    for i in itertools.count():
        yield env.timeout(1)
        
        # randomly select a ship type from SHIP_DISTR
        shiptype = random.choice(SHIP_DISTR)
        env.process(ship('Ship %d' % i, env, tug, dock, shiptype))

def ship(name, env, tug, dock, shiptype):
    # waiting time
    wt = 0
    
    yield env.process(shipAtPort(name, env, tug, dock))
    
    print('%s arriving at port at %.1f' % (name, env.now))
    with tug.request() as req:
        # Request the tug
        wt = env.now
        yield req
        wt = env.now - wt

        #port_waiting_time.
        port_waiting_time.append(wt)

        print('%s waiting at port for tug at %.1f' % (name, env.now))
        # Tug transport to dock takes 1h
        yield env.process(tug_transport(name, env, tug, shiptype))
        print('%s brought to dock at %.1f' % (name, env.now))
        
        # request for dock and process ship at dock
        env.process(shipAtDock(name, env, dock, shiptype))

def shipAtPort(name, env, tug, dock):
    """Generate new ships that arrive at the port."""
    # normal distribution (mean:11, sigma:1)
    yield env.timeout(random.normalvariate(AVG_TRAVEL_TYPE1_3, 1))
        
def tug_transport(name, env, tug, shiptype):
    """Arrives at the port or the dock after a 1h delay and transports the ship."""
    # print('Tug starts %s transport at %.1f' % (name, env.now))
    yield env.timeout(TUG_TIME_ONE_WAY)
    # print('Tug stops %s transport at %.1f' % (name, env.now))


        
def shipAtDock(name, env, dock, shiptype):
    # unload time    
    ut = 0
    with dock.request() as req:
        # Request a dock
        yield req
        
        unloadTime = {
                1 : UNLOAD_TIME_TYPE_1,
                2 : UNLOAD_TIME_TYPE_2,
                3 : UNLOAD_TIME_TYPE_3,
                4 : UNLOAD_TIME_TYPE_4,
                  }
        print('%s of shiptype %d unloading at %.1f' % (name, shiptype, env.now))
        #yield env.timeout(random.uniform(*UNLOAD_TIME_TYPE_1))
        ut = env.now
        yield env.timeout(random.uniform(*unloadTime[shiptype]))
        print('%s unloaded at %.1f' % (name, env.now))
        ut = env.now - ut
        load_sum.append(ut)
        
        with tug.request() as req:
            # Request the tug
            yield req

            # Tug transport takes 1h
            print('%s waiting at dock for tug at %.1f' % (name, env.now))
            yield env.process(tug_transport(name, env, tug, shiptype))
            print('%s brought back to port at %.1f' % (name, env.now))



# Setup and start the simulation
print('Ship unload Simulation')
random.seed(RANDOM_SEED)

# Create environment and start processes
env = simpy.Environment()

# ships_type_4 = simpy.Resource(env, 1)

# Resource with capacity of usage slots that can be requested by processes.
tug = simpy.Resource(env, TUGS)

# Resource with capacity of usage slots that can be requested by processes.
dock = simpy.Resource(env, DOCKS)


"""--- comment this line to simulate without shiptype 4 ---"""
ships_type_4 = simpy.Container(env, SHIPS_TYPE_4, init=SHIPS_TYPE_4)

# Process an event yielding generator.
env.process(ship_generator(env, tug, dock))

"""--- comment this line to simulate without shiptype 4 ---"""
env.process(ship_generator_type_4(env, tug, dock, ships_type_4))

# Execute!
env.run(until=SIM_TIME)

print('avg. waiting time at port: ', np.mean(port_waiting_time))
print('unloaded freight: ', np.sum(load_sum))
# swarm_formation_sim
A collection of swarm robot formation simulations using Python and Pygame. I have done [swarm robot simulations in ROS](https://github.com/yangliu28/swarm_robot_ros_sim.git) before, but the combination of Python and Pygame turns out to be a nice fit for my simulations, plus the simpilicity in programming the alogrithms and implementing the graphics.

## Contents
All the formation control algorithms simulated here agree on a few conditions of the robots. The robots can sensing relative position of neighbors with in sensing range. The robots can communicate with robots in communication range. Both sensing range and communication range are very small, most time they are treated the same in the simulations. (This corresponds to the physical infrared sensor that does sensing and communicating at same time.) The robot swarm is homogeneous. The robots can do omnidirectional movements. The robots are modelled as dots, so no collision avoidance method is studied here.

Line formation simulation 1 features climbing method and competing mechanism. Refer "line_formation_1.py" for more details.

Line formation simulation 2 is similar to the first line formation, except implementing merging method instead of climbing to form the line. Refer "line_formation_2.py" for more details.

## Run the simulations

Install correct Pygame version for your Python.

Run the line formation simulation with climbing method:

`python line_formation_1.py`

Run the line formation simulation with merging method:

`python line_formation_2.py`



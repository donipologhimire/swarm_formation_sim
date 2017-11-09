# This simulation tests the probabilistic convergence algorithm (a collective decision
# making algorithm) on randomly generated 2D honeycomb network. The algorithm is extracted
# from previous loop reshape simulations for further testing, so that it can be generally
# used on 2D random network topologies. The distribution evolution method is very similiar
# except that more than three nodes are involved in the weighted averaging process.

# input arguments:
# '-f': filename of the honeycomb network
# '-d': number of decisions each node can choose from

# Pygame will be used to animate the dynamic subgroup changes in the network;
# Matplotlib will be used to draw the unipolarity in a 3D bar graph, the whole decision
# distribution is not necessary.

# Algorithm to update the subgroups in 2D honeycomb network:
# Using a pool of indices for nodes that have not been subgrouped, those labeled into a
# subgroup will be remove from the pool. As long as the pool is not enpty, a while loop
# will continue searching subgroups one by one. In the loop, it initialize a new subgroup
# with first node in the pool. It also initialize a fifo-like variable(p_members) for
# potential members of this subgroup, and an index variable(p_index) for iterating through
# the potential members. If p_members[p_index] doesn't share same decidion with first node,
# p_index increases by 1, will check next value in p_members. If it does, then a new member
# for this subgroup has been found, it will be removed from the pool and p_members, and added
# to current subgroup. The new subgroup member will also introduce its neighbors as new
# potential members, but they should not be in p_members and current subgroup, and should be
# in node pool. The member search for this subgroup will end if p_index iterates to the end
# of p_members.
# Implementation of this algorithm is inside the simulation loop.


import pygame
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from network_generator_2D_swarm import *
from formation_functions import *
import math, sys, os, getopt, time
import numpy as np


net_size = 30  # default size of the honeycomb network
net_folder = 'honeycomb-networks'  # folder for all network files
net_filename = '30-1'  # defautl filename of the network file, if no input
net_filepath = os.path.join(os.getcwd(), net_folder, net_filename)  # corresponding filepath

deci_num = 30  # default number of decisions each node can choose from

# read command line options
try:
    opts, args = getopt.getopt(sys.argv[1:], 'f:d:')
    # The colon after 'f' means '-f' requires an argument, it will raise an error if no
    # argument followed by '-f'. But if '-f' is not even in the arguments, this won't raise
    # an error. So it's necessary to define the default network filename
except getopt.GetoptError as err:
    print str(err)
    sys.exit()
for opt,arg in opts:
    if opt == '-f':
        # get the filename of the network
        net_filename = arg
        # check if this file exists
        net_filepath = os.path.join(os.getcwd(), net_folder, net_filename)
        if not os.path.isfile(net_filepath):
            print "{} does not exist".format(net_filename)
            sys.exit()
        # parse the network size
        net_size = int(net_filename.split('-')[0])  # the number before first dash
    elif opt == '-d':
        # get the number of decisions
        deci_num = int(arg)

# read the network from file
nodes = []  # integers only is necessary to describe the network's node positions
f = open(net_filepath, 'r')
new_line = f.readline()
while len(new_line) != 0:  # not the end of the file yet
    pos_str = new_line[0:-1].split(' ')  # get rid of '\n' at end
    pos = [int(pos_str[0]), int(pos_str[1])]  # convert to integers
    nodes.append(pos)
    new_line = f.readline()

# generate the connection matrix, 0 for not connected, 1 for connected
connections = [[0 for j in range(net_size)] for i in range(net_size)]  # all zeros
for i in range(net_size):
    for j in range(i+1, net_size):
        # find if nodes[i] and nodes[j] are neighbors
        diff_x = nodes[i][0] - nodes[j][0]
        diff_y = nodes[i][1] - nodes[j][1]
        if abs(diff_x) + abs(diff_y) == 1 or diff_x * diff_y == -1:
            # condition 1: one of the axis value difference is 1, the other is 0
            # condition 2: one of the axis value difference is 1, the other is -1
            connections[i][j] = 1
            connections[j][i] = 1
# another list type variable for easy indexing from each node
# converted from the above connection matrix variable
connection_lists = []  # the lists of connecting nodes for each node
for i in range(net_size):
    connection_list_temp = []
    for j in range(net_size):
        if connections[i][j]: connection_list_temp.append(j)
    connection_lists.append(connection_list_temp)

# plot the network as dots and lines in pygame window
pygame.init()  # initialize the pygame
# find appropriate window size from current network
# convert node positions from honeycomb coordinates to Cartesian coordinates, for plotting
nodes_plt = np.array([honeycomb_to_cartesian(pos) for pos in nodes])
(xmin, ymin) = np.amin(nodes_plt, axis=0)
(xmax, ymax) = np.amax(nodes_plt, axis=0)
world_size = (xmax-xmin + 2.0, ymax-ymin + 2.0)  # extra length for clearance
pixels_per_length = 50  # resolution for converting from world to display
# display origin is at left top corner
screen_size = (int(round(world_size[0] * pixels_per_length)),
               int(round(world_size[1] * pixels_per_length)))
background_color = (0,0,0)
node_color = (255,0,0)  # red for nodes as dots
connection_color = [0,0,255]  # blue for regular connecting lines
subgroup_color = (255,255,0)  # yellow for connecting lines in the subgroups
node_size = 5  # node modeled as dot, number of pixels for radius
# set up the simulation window and surface object
icon = pygame.image.load("icon_geometry_art.jpg")
pygame.display.set_icon(icon)
screen = pygame.display.set_mode(screen_size)
pygame.display.set_caption("Probabilistic Convergence of 2D Honeycomb Network")

# shift the node display positions to the middle of the window
centroid_temp = np.mean(nodes_plt, axis=0)
nodes_plt = nodes_plt - centroid_temp + (world_size[0]/2.0, world_size[1]/2.0)
nodes_disp = [world_to_display(nodes_plt[i], world_size, screen_size)
              for i in range(net_size)]

# draw the network for the first time
screen.fill(background_color)
# draw the connecting lines
for i in range(net_size):
    for j in range(i+1, net_size):
        if connections[i][j]:
            pygame.draw.line(screen, node_color, nodes_disp[i], nodes_disp[j])
# draw the nodes as dots
for i in range(net_size):
    pygame.draw.circle(screen, node_color, nodes_disp[i], node_size, 0)
pygame.display.update()

############### the probabilistic convergence ###############

# variable for decision distribution of all individuals
deci_dist = np.random.rand(net_size, deci_num)
# normalize the random numbers such that the sum is 1.0
sum_temp = np.sum(deci_dist, axis=1)
for i in range(net_size):
    deci_dist[i][:] = deci_dist[i][:] / sum_temp[i]
# variable for the dominant decision for all nodes
deci_domi = np.argmax(deci_dist, axis=1)
# only adjacent block of nodes sharing same dominant decision belongs to same subgroup
subgroups = []  # seperate lists of node indices for all subgroups
subsizes = [0 for i in range(net_size)]  # the subgroup size that each node belongs to
# Difference of two distributions is the sum of absolute values of differences
# of all individual probabilities.
# Overflow threshold for the distribution difference. Distribution difference larger than
# this means neighbors are not quite agree with each other, so no further improvement on
# unipolarity will be performed. If distribution difference is lower than the threshold,
# linear multiplier will be used to improve unipolarity on the result distribution.
dist_diff_thres = 0.3
# Variable for ratio of distribution difference to distribution difference threshold.
# The ratio is in range of [0,1], it will be used for constructing the corresponding linear
# multiplier. At one side, the smaller the ratio, the smaller the distribution difference,
# and faster the unipolarity should increase. At the other side, the ratio will be positively
# related to the small end of the linear multiplier. The smallee the ratio gets, the steeper
# the linear multiplier will be, and the faster the unipolarity increases.
dist_diff_ratio = [0.0 for i in range(net_size)]
# Exponent of a power function to map the distribution difference ratio to a larger value,
# and therefore slow donw the growing rate.
dist_diff_power = 0.3

# start the matplotlib window first before the simulation cycle
fig = plt.figure()
fig.canvas.set_window_title('Unipolarity of 2D Honeycomb Network')
ax = fig.add_subplot(111, projection='3d')
x_pos = [pos[0] for pos in nodes_plt]  # the positions of the bars
y_pos = [pos[1] for pos in nodes_plt]
z_pos = np.zeros(net_size)
dx = 0.5 * np.ones(net_size)  # the sizes of the bars
dy = 0.5 * np.ones(net_size)
dz = np.zeros(net_size)
fig.canvas.draw()
fig.show()

# the simulation cycle
sim_exit = False  # simulation exit flag
sim_pause = True  # simulation pause flag
iter_count = 0
time_now = pygame.time.get_ticks()  # return milliseconds
time_last = time_now  # reset as right now
time_period = 500  # desired simulation period, will jump the delay if period overflow
while not sim_exit:
    # exit the program by close window button, or Esc or Q on keyboard
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sim_exit = True  # exit with the close window button
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                sim_pause = not sim_pause  # reverse the pause flag
            if (event.key == pygame.K_ESCAPE) or (event.key == pygame.K_q):
                sim_exit = True  # exit with ESC key or Q key

    # skip the rest if paused
    if sim_pause: continue

    # prepare information for the decision distribution evolution
    # including 1.dominant decisions, 2.subgroups, and 3.subgroup sizes

    # 1.update the dominant decision for all nodes
    deci_domi = np.argmax(deci_dist, axis=1)

    # 2.update the subgroups
    subgroups = []  # empty the subgroups container
    # a diminishing global pool for node indices, for nodes not yet assigned into subgroups
    n_pool = range(net_size)
    # start searching subgroups one by one from the global node pool
    while len(n_pool) != 0:
        # start a new subgroup, with first node in the n_pool
        first_member = n_pool[0]  # first member of this subgroup
        subgroup_temp = [first_member]  # current temporary subgroup
        n_pool.pop(0)  # pop out first node in the pool
        # a list of potential members for current subgroup
        # this list may increase when new members of subgroup are discovered
        p_members = connection_lists[first_member][:]
        # an index for iterating through p_members, in searching subgroup members
        p_index = 0  # if it climbs to the end, the searching ends
        # index of dominant decision for current subgroup
        current_domi = deci_domi[first_member]
        # dynamically iterating through p_members with p_index
        while p_index < len(p_members):  # index still in valid range
            if deci_domi[p_members[p_index]] == current_domi:
                # a new member has been found
                new_member = p_members[p_index]  # get index of the new member
                p_members.remove(new_member)  # remove it from p_members list
                    # but not increase p_index, because new value in p_members will flush in
                n_pool.remove(new_member)  # remove it from the global node pool
                subgroup_temp.append(new_member)  # add it to current subgroup
                # check if new potential members are available, due to new node discovery
                p_members_new = connection_lists[new_member]  # new potential members
                for member in p_members_new:
                    if member not in p_members:  # should not already in p_members
                        if member not in subgroup_temp:  # should not in current subgroup
                            if member in n_pool:  # should be available in global pool
                                # if conditions satisfied, it is qualified as a potential member
                                p_members.append(member)  # append at the end
            else:
                # a boundary node(share different decision) has been met
                # leave it in p_members, will help to avoid checking back again on this node
                p_index = p_index + 1  # shift right one position
        # all connected members for this subgroup have been located
        subgroups.append(subgroup_temp)  # append the new subgroup
        # the end of searching for one subgroup

    # 3.update the subgroup size each node is in
    traverse_list = range(net_size)  # remove when debugged
         # used to check if all nodes have been assigned a subgroup size
    for sub in subgroups:
        size_temp = len(sub)
        for i in sub:
            subsizes[i] = size_temp
            traverse_list.remove(i)
    if len(traverse_list) != 0:
        print("subgroup sizes check error")
        sys.exit()

    # the decision distribution evolution
    deci_dist_t = np.copy(deci_dist)  # deep copy of the 'deci_dist'
    for i in range(net_size):
        host_domi = deci_domi[i]
        converged = True
        for neighbor in connection_lists[i]:
            if host_domi != deci_domi[neighbor]:
                converged = False
                break
        # action based on convergence of dominant decision
        if converged:  # all neighbors have converged with host
            # step 1: take equally weighted average on all distributions
            # including host and all neighbors
            deci_dist[i] = deci_dist_t[i]*1.0  # start with host itself
            for neighbor in connection_lists[i]:
                # accumulate neighbor's distribution
                deci_dist[i] = deci_dist[i] + deci_dist_t[neighbor]
            # normalize the distribution such that sum is 1.0
            sum_temp = np.sum(deci_dist[i])
            deci_dist[i] = deci_dist[i] / sum_temp
            # step 2: increase the unipolarity by applying the linear multiplier
            # (this step is only for when all neighbors are converged)
            # First find the largest difference between two distributions in this block
            # of nodes, including the host and all its neighbors.
            comb_pool = [i] + connection_lists[i]  # add host to a pool with its neighbors
                # will be used to form combinations from this pool
            comb_pool_len = len(comb_pool)
            dist_diff = []
            for j in range(comb_pool_len):
                for k in range(j+1, comb_pool_len):
                    j_node = comb_pool[j]
                    k_node = comb_pool[k]
                    dist_diff.append(np.sum(abs(deci_dist[j_node] - deci_dist[k_node])))
            dist_diff_max = max(dist_diff)  # maximum distribution difference of all
            if dist_diff_max < dist_diff_thres:
                # distribution difference is small enough,
                # that linear multiplier should be applied to increase unipolarity
                dist_diff_ratio = dist_diff_max/dist_diff_thres
                # Linear multiplier is generated from value of smaller and larger ends, the
                # smaller end is positively related with dist_diff_ratio. The smaller the
                # maximum distribution difference, the smaller the dist_diff_ratio, and the
                # steeper the linear multiplier.
                # '1.0/deci_num' is the average value of the linear multiplier
                small_end = 1.0/deci_num * np.power(dist_diff_ratio, dist_diff_power)
                large_end = 2.0/deci_num - small_end
                # sort the magnitude of the current distribution
                dist_temp = np.copy(deci_dist[i])  # temporary distribution
                sort_index = range(deci_num)
                for j in range(deci_num-1):  # bubble sort, ascending order
                    for k in range(deci_num-1-j):
                        if dist_temp[k] > dist_temp[k+1]:
                            # exchange values in 'dist_temp'
                            temp = dist_temp[k]
                            dist_temp[k] = dist_temp[k+1]
                            dist_temp[k+1] = temp
                            # exchange values in 'sort_index'
                            temp = sort_index[k]
                            sort_index[k] = sort_index[k+1]
                            sort_index[k+1] = temp
                # applying the linear multiplier
                for j in range(deci_num):
                    multiplier = small_end + float(j)/(deci_num-1) * (large_end-small_end)
                    deci_dist[i][sort_index[j]] = deci_dist[i][sort_index[j]] * multiplier
                # normalize the distribution such that sum is 1.0
                sum_temp = np.sum(deci_dist[i])
                deci_dist[i] = deci_dist[i]/sum_temp
            else:
                # not applying linear multiplier when distribution difference is large
                pass
        else:  # at least one neighbor has different opinion with host
            # take unequal weights in the averaging process based on subgroup sizes
            deci_dist[i] = deci_dist_t[i]*subsizes[i]  # start with host itself
            for neighbor in connection_lists[i]:
                # accumulate neighbor's distribution
                deci_dist[i] = deci_dist[i] + deci_dist_t[neighbor]*subsizes[neighbor]
            # normalize the distribution
            sum_temp = np.sum(deci_dist[i])
            deci_dist[i] = deci_dist[i] / sum_temp

    # graphics animation, both pygame window and matplotlib window
    # 1.pygame window for dynamics of network's subgroups
    screen.fill(background_color)
    # draw the regualr connecting lines
    for i in range(net_size):
        for j in range(i+1, net_size):
            if connections[i][j]:
                pygame.draw.line(screen, connection_color,
                                 nodes_disp[i], nodes_disp[j], 2)
    # draw the connecting lines marking subgroups
    for sub in subgroups:
        sub_len = len(sub)
        for i in range(sub_len):
            for j in range(i+1, sub_len):
                i_node = sub[i]
                j_node = sub[j]
                # check if two nodes in one subgroup is connected
                if connections[i_node][j_node]:
                    # wider lines for subgroup connections
                    pygame.draw.line(screen, subgroup_color,
                                     nodes_disp[i_node], nodes_disp[j_node], 3)
    # draw the nodes as dots
    for i in range(net_size):
        pygame.draw.circle(screen, node_color, nodes_disp[i], node_size, 0)
    pygame.display.update()
    # 2.matplotlib window for 3D bar graph of unipolarity of decision distribution
    dz = [deci_dist[i][deci_domi[i]] for i in range(net_size)]
    ax.bar3d(x_pos, y_pos, z_pos, dx, dy, dz, color='b')
    fig.canvas.draw()
    fig.show()

    # simulation updating frequency control
    time_now = pygame.time.get_ticks()
    time_past = time_now - time_last  # time past since last time_last
    # needs to delay a bit more if time past has not reach desired period
    # will skip if time is overdue
    if time_now - time_last < time_period:
        pygame.time.delay(time_period-time_past)
    time_last = pygame.time.get_ticks()  # reset time-last
    # iteration count
    print "iteration {}".format(iter_count)
    iter_count = iter_count + 1





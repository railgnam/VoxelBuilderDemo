from voxel_builder_library import *
from show_voxel_plt import *
from helpers import *
from show_voxel_plt import timestamp_now
from matplotlib import animation
save_animation = False

voxel_size = 60
agent_count = 10
iterations = 1000
save_ = False
save_json_in_steps = False
title_ = 'img'
note = 'build_probability_a%s_i%s' %(agent_count, iterations)
time__ = timestamp_now

global smell_layer, ground, agents

agent_space = Layer(voxel_size=voxel_size, rgb=[34/255, 116/255, 240/255])
queen_space = Layer(voxel_size=voxel_size, rgb=[203/255, 21/255, 207/255])
# track_layer = Layer(voxel_size=voxel_size, rgb=[147/255, 209/255, 237/255])
smell_layer = Layer(voxel_size=voxel_size, rgb=[240/255, 220/255, 150/255], diffusion_ratio=1/6, decay_ratio=0.01)
wait_to_diffuse = 5

# create ground:
ground_level_Z = 0
ground = Layer(voxel_size=voxel_size, name='Ground')
ground.array = make_solid_box_z(voxel_size, ground_level_Z)
wall = make_solid_box_xxyyzz(voxel_size, 20,23,20,23,0,3)
ground.array += wall
ground.rgb = [207/255, 179/255, 171/255]

# move_preference settings w pheromon weights
ground_smell_ph_w = 0
random_ph_w = 0.2
up_pref_ph_w = 1
side_move_pref_ratio = 0.5

# BUILD SETTINGS
construction_on = True
# construct_limit_1 = 0.01
# construct_limit_2 = 0.09
construct_limit_1 = 0.005
construct_limit_2 = 0.05
queen_build_weigth = 1

# build probability settings
add_prob = 0.8
climb = 0.5
top = 2
walk = 0.1
descend = -0.05
build_probability_limit = 1

build_roof = -1
build_aside = -1
build_above = 1

# make agents
agents = []
for i in range(agent_count):
    agent = Agent(
        space_layer = agent_space, ground_layer = ground, construction_layer = ground,
        track_layer = None, leave_trace=False, save_move_history=True)
    x = np.random.randint(0, voxel_size)
    y = np.random.randint(0, voxel_size)
    agent.pose = [x,y,1]
    agents.append(agent)

# make queen
queens = []
poses = [[40,40], [30,15]]
for i in range(2):
    queen = Agent(space_layer = queen_space, ground_layer = ground)
    x,y = poses[i]
    queen.pose = [x,y,1]
    queen.update_space()

# pre_smells
for i in range(wait_to_diffuse):
    smell_layer.emission_intake(ground.array, 2, False)
    smell_layer.diffuse()
    smell_layer.gravity_shift(5, 0.8)
    smell_layer.decay()
    ground.block_layers([smell_layer])

# run as simulation
def animate(frame):
# for i in range(iterations):
    # if animate.counter % 20 == 0:
    print(animate.counter)
    # queen odor
    smell_layer.emission_intake(queen_space.array, 2, False)
    smell_layer.diffuse()
    smell_layer.gravity_shift(5, 2)
    smell_layer.decay()
    ground.block_layers([smell_layer])

    # move and build
    for agent in agents:
        reset_agent = False
        queen_smell_ph = agent.get_nb_26_cell_values(smell_layer, agent.pose) * ground_smell_ph_w
        random_ph = agent.random_pheromones(26) * random_ph_w
        up_pref_ph = agent.direction_preference_26_pheromones(side_move_pref_ratio) * up_pref_ph_w
        pheromone_cube = random_ph * 2 + queen_smell_ph + up_pref_ph * 0.5
        moved = agent.follow_pheromones(pheromone_cube)

        # move based on climb style
        if moved:
            # check move style
            # agent.analyze_move_history()
            # add probability per style
            agent.add_build_propability_by_pheromone_density(queen_smell_ph, queen_build_weigth, construct_limit_1, construct_limit_2)
            agent.add_build_probability_by_move_history(add_prob, climb, top, walk, descend)
            below, aside, above = agent.analyze_position(ground)
            if below: agent.build_probability += build_roof
            if aside: agent.build_probability += build_aside
            if above: agent.build_probability += build_above
            # build
            if construction_on:
                # flag = agent.get_build_flag_by_pheromones(smell_layer, construct_limit_1, construct_limit_2 )
                # if flag:
                if agent.build_probability >= build_probability_limit:
                    built = agent.build()
                    if built: 
                        reset_agent = True

        elif not moved:
            # stuck in position: reset
            reset_agent = True
        
        if reset_agent:
            x = np.random.randint(0, voxel_size)
            y = np.random.randint(0, voxel_size)
            agent.pose = [x,y,1]
            agent.build_probability = 0
            agent.move_history = []

    print('done')

    # SHOW
    a1 = ground.array.copy()
    a1[:,:,0] = 0

    # show SCATTER PLOT
    pts_built = convert_array_to_points(a1, False)
    # pts_agent_space = convert_array_to_points(agent_space.array, False)
    arrays_to_show = [pts_built]
    colors = [ground.rgb]
    # arrays_to_show = [pts_built, pts_agent_space]
    # colors = [ground.rgb, agent_space.rgb]
    for array, color in zip(arrays_to_show, colors):
        p = array.transpose()
        axes.scatter(p[0, :], p[1, :], p[2, :], marker = 's', s = 1, facecolor = color)
    c = animate.counter
    # # save as point_list
    if save_json_in_steps:
        if c % 5 == 0:
            filename = 'scr/data/point_lists/pts_built_%s_%s_i-%s.json' %(time__, note, c)
            with open(filename, 'w') as file:
                list_to_dump = convert_array_to_points(ground.array, True)
                json.dump(list_to_dump, file)
            print('\nptlist saved as %s:\n' %filename)
    
    animate.counter += 1

scale = voxel_size
fig = plt.figure(figsize = [4, 4], dpi = 200)
axes = plt.axes(xlim=(0, scale), ylim =  (0, scale), zlim = (0, scale), projection = '3d')
axes.set_xticks([])
axes.set_yticks([])
axes.set_zticks([])
# a1 = ground.array
# a1[:,:,0] = 0
# ground.array = a1
p = ground.array.transpose()
axes.scatter(p[0, :], p[1, :], p[2, :], marker = 's', s = 1, facecolor = ground.rgb)

animate.counter = 0
anim = animation.FuncAnimation(fig, animate, frames=iterations, interval = 1)
# if save_animation:
#     anim.save('img/gif/%s_%s_%s.gif' %(title_, timestamp_now, note))
#     print('saved_anim')
if save_:
    plt.savefig('img/%s_%s_%s.png' %(title_, timestamp_now, note), bbox_inches='tight', dpi = 200)
    print('saved img')

# # save as point_list
if save_:
    filename = 'scr/data/point_lists/pts_%s_%s.json' %(time__, note)
    with open(filename, 'w') as file:
        list_to_dump = convert_array_to_points(ground.array, True)
        json.dump(list_to_dump, file)
    print('\nptlist saved as %s:\n' %filename)

plt.show()
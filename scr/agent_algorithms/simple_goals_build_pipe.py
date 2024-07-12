#pass
from voxel_builder_library import pheromon_loop, make_solid_box_z, make_solid_box_xxyyzz
from class_agent import Agent
from class_layer import Layer
# from voxel_builder_library import get_chance_by_climb_style, get_chance_by_relative_position, get_chances_by_density
import numpy as np

"""
DESIGN INTENTION

fill up the edges

# notes:
clay_layer: represent clay volume, float array, decays linearly per age.
ground_layer: contains clay volume + floor, is integrer array, doesnt decay
when build, both is built.
ground_layer is used for blocking air and movement.
"""

# overal settings
voxel_size = 30
agent_count = 5

# setup variables
# agent enter:
enter_zone = [0, 10, 0, 10]
# wall_params = [20,25,20,25, 0, 20] # x1,x2,y1,y2,z1,z2

# BUILD SETTINGS
reach_to_build = 0.9
reach_to_erase = 1000
stacked_chances = False
reset_after_build = True

# edge analysis variables:
min_in_level = 2
min_below = 7

# MOVE_PRESETS
random_pheromon_weigth = 0
queen_layer_pheromon_weigth = -1.5

move_up = 1
move_side = 0.8
move_down = 0.1
move_preference_weigth = 0


""" ENVIRONMENT:
layers = [agent_space, air_layer, clay_layer, ground_layer, queen_pheromon, queen_coloum_array]
settings = [agent_count, voxel_size]

agent_space, air_layer, clay_layer, ground_layer, queen_pheromon, queen_coloum_array = layers
agent_count, voxel_size : settings
"""

def layer_env_setup(iterations):
    """
    creates the simulation environment setup
    with preset values in the definition
    
    returns: [settings, layers, clai_moisture_layer]
    layers = [agent_space, air_layer, build_boundary_pheromon, clay_layer,  ground_layer, queen_bee_pheromon, sky_ph_layer]
    settings = [agent_count, voxel_size]
    """
    ### LAYERS OF THE ENVIRONMENT
    rgb_sky = [29, 77, 222]
    rgb_agents = [34,116,240]
    rgb_clay = [167, 217, 213]
    rgb_air = [200, 204, 219]
    rgb_ground_layer = [207, 179, 171]

    ground_layer = Layer(voxel_size=voxel_size, name='ground_layer', rgb = [i/255 for i in rgb_ground_layer])
    agent_space = Layer('agent_space', voxel_size = voxel_size, rgb = [i/255 for i in rgb_agents])
    clay_layer = Layer('clay_layer', voxel_size, rgb = [i/255 for i in rgb_clay])
    air_layer = Layer('air_layer', voxel_size, rgb = [i/255 for i in rgb_air])
    queen_pheromon = Layer('queen_pheromon', voxel_size, rgb = [i/255 for i in rgb_sky])
    # clay_layer.decay_linear_value = 1 / iterations / agent_count / 2
    queen_coloum_array = make_solid_box_xxyyzz(voxel_size,10,11,10,11,0,40)
    # air_layer.diffusion_ratio = 1/7
    # air_layer.decay_ratio = 1/5
    # air_layer.gradient_resolution = 1000000
    queen_pheromon.diffusion_ratio = 1/7
    queen_pheromon.decay_ratio = 1/10
    queen_pheromon.emission_factor = 0.5
    queen_pheromon.emission(queen_coloum_array)
    queen_pheromon.diffuse()
    queen_pheromon.decay()

    ### CREATE ENVIRONMENT
    # make ground_layer
    ground_layer_level_Z = 0
    ground_layer.array = make_solid_box_z(voxel_size, ground_layer_level_Z)
    clay_layer.array += ground_layer.array

    # WRAP ENVIRONMENT
    layers = [agent_space, air_layer, clay_layer, ground_layer, queen_pheromon, queen_coloum_array]
    settings = [agent_count, voxel_size]
    return settings, layers, clay_layer

"""DIFFUSION:
clay layer decays (dries)
clay layer emits pheromons into the air layer"""

def diffuse_environment(layers):
    """clay layer decays (dries)
    clay layer emits pheromons into the air layer"""
    agent_space, air_layer, clay_layer, ground_layer, queen_pheromon, queen_coloum_array = layers
    clay_layer.decay_linear()
    pheromon_loop(queen_pheromon, emmission_array = queen_coloum_array, blocking_layer = ground_layer)
    pass

"""Setup:
enter from the bottom_left corner
corner size = enter_corner_width
"""
def setup_agents(layers):
    agent_space = layers[0]
    ground_layer = layers[3]
    agents = []
    for i in range(agent_count):
        # create object
        agent = Agent(
            space_layer = agent_space, 
            ground_layer = ground_layer,
            save_move_history=False)
        # drop in the corner
        reset_agent(agent, voxel_size, enter_zone)

        agents.append(agent)
    return agents

def reset_agent(agent, voxel_size, enter_zone):
    # centered setup
    a,b,c,d = enter_zone
    x = np.random.randint(a, b)
    y = np.random.randint(c, d)
    agent.pose = [x,y,1]

    # agent.build_chance = 0
    # agent.erase_chance = 0
    agent.move_history = []


def move_agent(agent, layers):
    """move agents in a direction, based on several pheromons weighted in different ratios.
    1. random direction pheromon
    2. queen_bee_pheromon = None : Layer class object,
    3. sky_ph_layer = None : Layer class object,
    4. air_layer
    5. world direction preference pheromons

    Input:
        agent: Agent class object
        queen_bee_pheromon = None : Layer class object,
        sky_ph_layer = None : Layer class object,
        air_layer = None : Layer class object,
        None layers are passed
    further parameters are preset in the function

    return True if moved, False if not


    """
    agent_space, air_layer, clay_layer, ground_layer, queen_pheromon, queen_coloum_array = layers

    # agent_space, air_layer, clay_layer,  ground_layer = layers
    queen_pheromon = layers[4]

    # add pheromon attractors
    pose = agent.pose
    # random
    cube = agent.random_pheromones(26) * random_pheromon_weigth
    # air
    cube += agent.get_nb_26_cell_values(queen_pheromon, pose) * queen_layer_pheromon_weigth

    # add direction prerence
    cube += agent.direction_preference_26_pheromones_v2(move_up, move_side, move_down) * move_preference_weigth
    
    # move
    moved = agent.follow_pheromones(cube, check_collision = False)

    return moved


    
        
def calculate_build_chances(agent, layers):
    """function operating with Agent and Layer class objects
    calculates probability of building and erasing voxels 
    combining several density analyses

    returns build_chance, erase_chance
    """
    build_chance = agent.build_chance
    erase_chance = agent.erase_chance
    
    # CHECK EDGE SITUATION
    ground_layer = layers[3]
    edge_bool = agent.check_edge_situation(ground_layer, in_level = min_in_level, below = min_below)
    if edge_bool:
        c = 2
        print('its and edge')
    else:
        c = 0
    e = 0
    build_chance += c
    erase_chance += e

    # clay_layer = layers[2]
    # Agent.check_edge_situation_v2(clay_layer, 1, 4)

    # # RELATIVE POSITION
    # c = agent.get_chance_by_relative_position(
    #     ground_layer,
    #     build_below = 2,
    #     build_aside = 1,
    #     build_above = 1,
    #     build_strength = 0.1)
    # build_chance += c

    # # surrrounding ground_layer_density
    # c, e = agent.get_chances_by_density(
    #         ground_layer,      
    #         build_if_over = 0,
    #         build_if_below = 15,
    #         erase_if_over = 21,
    #         erase_if_below = 30,
    #         build_strength = 1)
    # build_chance += c
    # erase_chance += e
    build_chance = 0
    erase_chance = 0
    print(build_chance, erase_chance)
    return build_chance, erase_chance

def build(agent, layers, build_chance, erase_chance, decay_clay = False):
    ground_layer = layers[3]
    clay_layer = layers[2]
    """agent builds on construction_layer, if pheromon value in cell hits limit
    chances are either momentary values or stacked by history
    return bool"""
    if stacked_chances:
        # print(erase_chance)
        agent.build_chance += build_chance
        agent.erase_chance += erase_chance
    else:
        agent.build_chance = build_chance
        agent.erase_chance = erase_chance

    # CHECK IF BUILD CONDITIONS are favorable
    built = False
    erased = False
    build_condition = agent.check_build_conditions(ground_layer)
    if agent.build_chance >= reach_to_build and build_condition == True:
        built = agent.build(ground_layer)
        built2 = agent.build(clay_layer)
        if built and reset_after_build:
            reset_agent = True
            if decay_clay:
                clay_layer.decay_linear()
    elif agent.erase_chance >= reach_to_erase and build_condition == True:
        erased = agent.erase(ground_layer)
        erased2 = agent.erase(clay_layer)
    # else: 
    #     built = False
    #     erased = False
    return built, erased

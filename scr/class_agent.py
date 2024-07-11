from voxel_builder_library import *
from voxel_builder_library import direction_dictonary as dir_dict
class Agent:
    def __init__(self, 
        pose = [0,0,0], 
        ground_layer = None,
        space_layer = None,
        track_layer = None,
        leave_trace = False,
        save_move_history = True):
        self.pose = np.asarray(pose)  # [i,j,k]
        self.leave_trace = leave_trace
        self.space_layer = space_layer
        self.track_layer = track_layer
        self.ground_layer = ground_layer
        self.move_history = []
        self.save_move_history = save_move_history
        self.build_probability = 0
        if ground_layer != None:
            self.voxel_size = ground_layer.voxel_size
        self.cube_array = get_cube_array_indices()
        self._climb_style = ''
        self._build_chance = 0
        self._erase_chance = 0

    @property
    def direction_dictonary(self):
        return dir_dict
    
    @property
    def direction_keys(self):
        return list(dir_dict.keys())

    @property
    def climb_style(self):
        self._climb_style = self.analyze_move_history()
        return self._climb_style
    
    @climb_style.setter
    def climb_style(self, value):
        if not isinstance(value, str):
            raise ValueError("Name must be a string")
        self._climb_style = value
    
    @property
    def build_chance(self):
        return self._build_chance
    
    @build_chance.setter
    def build_chance(self, value):
        if not isinstance(value, (float, int)):
            raise ValueError("Chance must be a number")
        self._build_chance = value
    
    @property
    def erase_chance(self):
        return self._erase_chance
    
    @erase_chance.setter
    def erase_chance(self, value):
        if not isinstance(value, (float, int)):
            raise ValueError("Chance must be a number")
        self._erase_chance = value

    def move(self, i, reintroduce = False):
        """move to a neighbor voxel based on the compas dictonary key index """
        v = self.direction_dictonary[self.direction_keys[i]]
        self.pose += v
        # reintroduce agent if n nonzero
        if reintroduce:
            self.pose = self.reintroduce_index(self.pose)
        else:
            self.pose = self.keep_index_in_bounds(self.pose)
        if self.save_move_history: 
            self.move_history.append(self.direction_keys[i])
    
    def move_26(self, dir, voxel_size = 0, keep_in_range_z = True, reintroduce = True):
        """move to a neighbor voxel based on dir vector """
        self.pose += dir
        # reintroduce agent if n nonzero
        n = voxel_size
        if keep_in_range_z:
            self.pose[2] = min(n, max(self.pose[2], 0))
        if reintroduce and voxel_size != 0:
            self.pose = np.mod(self.pose, np.asarray([n,n,n]))
        if self.save_move_history:
            if dir[2] == 1:
                self.move_history.append('up')
            elif dir[2] == 0:
                self.move_history.append('side')
            elif dir[2] == -1:
                self.move_history.append('down')

    def move_key(self, key, voxel_size = 0):
        """move to a neighbor voxel based on the compas dictonary key"""
        v = self.direction_dictonary[key]
        self.pose += v
        # reintroduce agent if n nonzero
        n = voxel_size
        if n != 0:
            self.pose = np.mod(self.pose, np.asarray([n,n,n]))
        if self.save_move_history: 
            self.move_history.append(key)

    def analyze_relative_position(self, layer):
        """check if there is sg around the agent
        return list of bool:
            [below, aside, above]"""
        # place = self.pose
        # f = direction_dictonary['front']
        # b = direction_dict_np['back']
        # l = direction_dict_np['left']
        # r = direction_dict_np['right']
        # u = direction_dict_np['up']
        # d = direction_dict_np['down']
        values = self.get_nb_6_cell_values(layer, self.pose)
        values = values.tolist()
        above = values.pop(0)
        below = values.pop(1)
        sides = sum(values)

        # print(above, below, sides)
        # self.direction_dictonary.keys()
        # above = layer.array[place + u]
        # print(above)
        # below = layer.array[place + d] 
        # sides = 0
        # for i in [f,b,r,l]:
        #     sides += layer.array[place + direction_dict_np['right']] 
        # sides = np.sum(sides)
        if sides > 0:
            aside = True
        else: 
            aside = False
        if above > 0:
            above = True
        else: 
            above = False
        if below > 0:
            below = True
        else: below = False
        self.relative_booleans_bottom_up = [below, aside, above] 
        return below, aside, above

#     def check_edge_situation_face(self, layer, in_level = 1, below = 9):
#         """returns checks if in edge situation v1
#         edge is defined by number of cells filled
#         and larger than [a] of 4 face nbs in level
#         larger than [b]  9 nbs below
# .
#         """
#         v = self.get_nb_26_cell_values(layer, self.pose, False)
#         # top = v[:9]
#         # mid = v[9:17]
#         down = v[17:]
#         u, f, r, b, l, d = self.direction_dictonary
#         mid = [f,r,b,l]
#         if sum(down) > below and sum(mid) > in_level:
#             return True
#         else:
#             return False
        
    def check_edge_situation(self, layer, in_level = 1, below = 9):
        """returns checks if in edge situation v1
        edge is defined by number of cells filled
        and larger than [a] of 8 nbs in level
        larger than [b]  9 nbs below"""
        v = self.get_nb_26_cell_values(layer, self.pose, False)
        print(v)
        # top = v[:9]
        mid = v[9:17]
        print(mid)
        down = v[17:]
        print(down)
        print(sum(down),sum(mid))
        if sum(down) > below and sum(mid) > in_level:
            return True
        else:
            return False

    def get_cube_array_indices(self, self_contain = False):
        """list of 26 neighbor cell indicies_list, 
        ordered per horizontal layers, top down, 
        counter clock wise, starting front, ending in the middle
        9 top + 8 middle + 9 bottom
        """
        # horizontal
        f = direction_dict_np['front']
        b = direction_dict_np['back']
        l = direction_dict_np['left']
        r = direction_dict_np['right']
        u = direction_dict_np['up']
        d = direction_dict_np['down']
        # first_story in level:
        story_1 = [f, f + r, r, b + r, b, b + l, l, f + l]
        story_0 = [i + d for i in story_1]
        story_2 = [i + u for i in story_1]
        if self_contain:
            nbs_w_corners = story_2 + [u] + story_1 + [np.asarray([0,0,0])] + story_0 + [d]
        else:
            nbs_w_corners = story_2 + [u] + story_1 + story_0 + [d]
        return nbs_w_corners


    def random_move(self, voxel_size = 0):
        i = np.random.randint(0,5)
        keys = self.direction_dictonary.keys()
        key = keys[i]
        self.move_key(key, voxel_size)
    
    def update_space(self):
        self.space_layer.set_layer_value_at_index(self.pose, 1)
    
    def random_pheromones(self, n = 6):
        return np.random.random(n)
    
    def direction_preference_6_pheromones(self, x = 0.5, up = True):
        """up = 1
        side = x
        down = 0.1"""
        if up:
            direction_preference = np.asarray([1, x, 0.1, x, x, x])
        else:
            direction_preference = np.ones(6)
        return direction_preference

    def direction_preference_26_pheromones(self, x = 0.5, up = True):
        """up = 1
        side = x
        down = 0.1"""
        if up:
            u = [1] * 9
            m = [x] * 8
            b = [0.1] * 9
            direction_preference =  np.asarray(u + m + b)
        else:
            direction_preference = np.ones(26)
        return direction_preference
    
    def direction_preference_26_pheromones_v2(self, up = 1, side = 0.5, down = 0):
        """up = 1
        side = x
        down = 0.1"""

        u = [up] * 9
        m = [side] * 8
        b = [down] * 9
        direction_preference =  np.asarray(u + m + b)
        return direction_preference
    
    def reintroduce_index(self, index):
        """returns index list as remainers of voxel size"""
        n = self.voxel_size
        x,y,z = index
        x = x % n
        y = y % n
        z = z % n
        return [x,y,z]

    def keep_index_in_bounds(self, index):
        """returns index list as remainers of voxel size"""
        n = self.voxel_size
        index = np.maximum(np.asarray([n,n,n]), np.asarray(index)).tolist()
        return index
    
    def get_nb_6_cell_indicies(self, pose, reintroduce = False):
        """returns the list of nb cell indexes"""
        nb_cell_index_list = []
        n = self.voxel_size
        for key in self.direction_dictonary.keys():
            d = self.direction_dictonary[key]
            place = d + pose
            if reintroduce:
                place = self.reintroduce_index(place)
            nb_cell_index_list.append( place)
        return nb_cell_index_list
    
    def get_nb_26_cell_indicies(self, pose, reintroduce = False):
        """returns the list of nb cell indexes
        ordered:
            horizontal layers downwards
            counter clock wise, starting front, ending in the middle
            9 top + 8 middle + 9 bottom"""
        nb_cell_index_list = []
        
        for d in self.cube_array:
            place = d + pose
            if reintroduce:
                place = self.reintroduce_index(place)
            nb_cell_index_list.append(d + pose)
        return nb_cell_index_list

    def get_nb_6_cell_values(self, layer, pose = None, reintroduce=True):
        # nb_value_dict = {}
        value_list = []
        for key in self.direction_dictonary.keys():
            d = self.direction_dictonary[key]
            nb_cell_index = d + pose
            # dont check index in boundary
            v = get_layer_value_at_index(layer, nb_cell_index, reintroduce)
            value_list.append(v)
        return np.asarray(value_list)
    
    def get_nb_26_cell_values(self, layer, pose = None, reintroduce = False):
        """returns the list of nb cell values
        if not reintroduced, out of bound values = 0
        ordered:
            horizontal layers downwards
            counter clock wise, starting front, ending in the middle
            9 top + 8 middle + 9 bottom
            """
        value_list = []
        for d in self.cube_array:
            nb_cell_index = d + pose
            v = get_layer_value_at_index(layer, nb_cell_index, reintroduce)
            value_list.append(v)
        return np.asarray(value_list)

    def scan_neighborhood_values(self, array, offset_radius = 1, pose = None, format_values = 0):
        """takes sub array around pose, in 'offset_radius'
        format values: returns sum '0', avarage '1', or all_values: 'None'"""
        if isinstance(pose, bool):
            pose = self.pose
        x,y,z = pose
        n = offset_radius
        v = array[x - n : x + n][y - n : y + n][z - n : z - n]
        if format_values == 0:
            return np.sum(v)
        elif format_values == 1:
            return np.average(v)
        elif format_values == 2:
            return v
        else: return v


    def get_cube_nbs_value_sums(self, layer, nb_pose):
        value_sum = 0
        nb_cube_array = self.cube_array + nb_pose
        for p in nb_cube_array:
            v = get_layer_value_at_index(layer, p)
            value_sum += v
        return value_sum
    
    def get_cube_nbs_value_sums_with_mask(self, layer, nb_pose):
        nb_cube_array = self.cube_array + nb_pose
        v = np.where(layer.array.indicies() == nb_cube_array, 1, 0)
        value_sum = np.sum(v)
        return value_sum

    def get_move_mask_6(self, ground_layer):
        """return ground directions as bools
        checks nbs of the nb cells
        if value > 0: return True"""
        # get nb cell indicies
        nb_cells = self.get_nb_6_cell_indicies(self.pose)
        cells_to_check = list(nb_cells)

        check_failed = []
        # iterate through nb cells
        for nb_pose in cells_to_check:
            # print('nb_pose;', nb_pose)
            # check nbs of nb cell
            nbs_values = self.get_nb_cell_values(ground_layer, nb_pose)
            # check nb cell
            nb_value = get_layer_value_at_index(ground_layer, nb_pose)
            if np.sum(nbs_values) > 0 and nb_value == 0:
                check_failed.append(False)
            else: check_failed.append(True)
        exclude_pheromones = np.asarray(check_failed)
        return exclude_pheromones
    
    def get_move_mask_26(self, ground_layer,  fly = False, reintroduce = True):
        """
        make logical_not mask
        check if agent can not move to the cell:
        to be able to move there: 
        1. cell must not be solid (grond_layer)
        2. cell must have a face nb with the ground layer
        
        return nb cells array, True if cant move 
        True if can not move there
            nb_cell != 0 or nb_value_sum = 0
        False if can move there:
            nb_cell == 0 and nb_value_sum > 0

        if fly == True, cells do not have to be neighbors of solid
        """
        # get nb cell indicies
        # nb_cells = self.get_nb_6_cell_indicies(self.pose)
        nb_cells = self.get_nb_26_cell_indicies(self.pose)
        cells_to_check = list(nb_cells)
        check_failed = []
        n = self.voxel_size
        # iterate through nb cells
        for nb_pose in cells_to_check:
            failed = True
            # dont check if nb cell is outside the boundary

            if reintroduce:
                # check if nb cell is empty
                nb_value = get_layer_value_at_index(ground_layer, nb_pose) 
                if nb_value == 0:
                    if not fly:
                        # check if nb cells have any face_nb cell which is solid
                        nbs_values = self.get_nb_6_cell_values(ground_layer, nb_pose)
                        if np.sum(nbs_values) > 0:
                            failed = False
                    else:
                        failed = False
            # check if nb cell is outside the boundary
            
            else:
                x,y,z = nb_pose
                if 0 <= x < n and 0 <= y < n and 0 <= z < n: 
                    # check if nb cell is empty
                    nb_value = get_layer_value_at_index(ground_layer, nb_pose) 
                    if nb_value == 0:
                        if not fly:
                            # check if nb cells have any face_nb cell which is solid
                            nbs_values = self.get_nb_6_cell_values(ground_layer, nb_pose)
                            if np.sum(nbs_values) > 0:
                                failed = False
                        else:
                            failed = False
            check_failed.append(failed)
        
        exclude_pheromones = np.asarray(check_failed)
        return exclude_pheromones
    

    def get_erase_mask_6(self, ground_layer):
        """
        make logical_not mask
        check if agent can erase the cell:
        to be able to erase::
        0. 3 x 3 nb cube of agent
        1. cell must be solid (grond_layer)
        2. cell must be in boundary
        return 26 nb cells array, True if cant erase 
        
        """
        # get nb cell indicies
        # nb_cells = self.get_nb_6_cell_indicies(self.pose)
        nb_cells = self.get_nb_6_cell_indicies(self.pose)
        cells_to_check = list(nb_cells)
        check_failed = []
        n = self.voxel_size
        # iterate through nb cells
        for nb_pose in cells_to_check:
            failed = True
            # check if nb cell is outside the boundary
            x,y,z = nb_pose
            if 0 <= x < n and 0 <= y < n and 0 <= z < n:
                # check if nb cell is empty
                nb_value = get_layer_value_at_index(ground_layer, nb_pose) 
                if nb_value == 1:
                    failed = False
            check_failed.append(failed)
        exclude_pheromones = np.asarray(check_failed)
        return exclude_pheromones
    

    def get_erase_mask_26(self, ground_layer):
        """
        make logical_not mask
        check if agent can erase the cell:
        to be able to erase::
        0. 3 x 3 nb cube of agent
        1. cell must be solid (grond_layer)
        2. cell must be in boundary
        return 26 nb cells array, True if cant erase 
        
        """
        # get nb cell indicies
        # nb_cells = self.get_nb_6_cell_indicies(self.pose)
        nb_cells = self.get_nb_26_cell_indicies(self.pose)
        cells_to_check = list(nb_cells)
        check_failed = []
        n = self.voxel_size
        # iterate through nb cells
        for nb_pose in cells_to_check:
            failed = True
            # check if nb cell is outside the boundary
            x,y,z = nb_pose
            if 0 <= x < n and 0 <= y < n and 0 <= z < n:
                # check if nb cell is empty
                nb_value = get_layer_value_at_index(ground_layer, nb_pose) 
                if nb_value == 1:
                    failed = False
            check_failed.append(failed)
        exclude_pheromones = np.asarray(check_failed)
        return exclude_pheromones
    
    def follow_pheromones(self, pheromone_cube, check_collision = False, fly = False, reintroduce = False):
        # check ground condition
        exclude_pheromones = self.get_move_mask_26(self.ground_layer, fly, reintroduce)
        pheromone_cube[exclude_pheromones] = -1
        
        if check_collision:
            # collision_array = self.space_layer.get_merged_array_with(self.ground_layer)
            exclude_pheromones = self.get_move_mask_26(self.space_layer, fly, reintroduce)
            pheromone_cube[exclude_pheromones] = -1
        
        if np.sum(pheromone_cube) == -26:
            print('cant move')
            return False

        # select best pheromon
        choice = np.argmax(pheromone_cube)
        # print('choice:', choice)
        move_vector = self.cube_array[choice]

        # update track layer
        if self.leave_trace:
            self.track_layer.set_layer_value_at_index(self.pose, 1)
        # update location in space layer
        self.space_layer.set_layer_value_at_index(self.pose, 0)

        # move
        self.move_26(move_vector, self.space_layer.voxel_size)

        # update location in space layer
        self.space_layer.set_layer_value_at_index(self.pose, 1)
        return True
    
    def get_build_flag_by_probability(self, limit):
        if limit < self.build_probability:
            return True
        else: 
            return False
    
    def get_build_flag_by_pheromones(self, pheromon_layer, limit1, limit2):
        """agent builds on construction_layer, if pheromon value in cell hits limit
        return bool"""
        v = get_layer_value_at_index(pheromon_layer, self.pose)
        # build
        if limit1 <= v <= limit2:
            return True
        else: 
            return False 

    def get_build_flag_after_history(self, last_step_NOR = ['up', 'down'], previous_steps_AND = ['up', 'up', 'up', 'up'], last_step_len = 1):
        """agent builds on construction_layer, if pheromon value in cell hits limit
        return bool"""
        x = -1 * last_step_len
        h = self.move_history
        l = len(previous_steps_AND) - x
        if len(h) < l: return False
        last_step = h[x]
        prev_steps = h[-l : x]
        # print(last_step, prev_steps)
        if last_step not in set(last_step_NOR) and prev_steps == previous_steps_AND:
            build_flag = True
            # print(prev_steps)
        else:
            build_flag = False
        return build_flag
    
    def analyze_move_history(self):
        last_moves = self.move_history[-3:]
        if last_moves == ['up', 'up', 'up']:
            climb_style = 'climb'
        elif last_moves == ['up', 'up', 'side']:
            climb_style = 'top'
        elif last_moves == ['side', 'side', 'side']:
            climb_style = 'walk' 
        elif last_moves == ['down', 'down', 'down']:
            climb_style = 'descend' 
        return climb_style      

    def add_build_probability_by_move_history(self, add = 1, climb = 0, top = 0, walk = 0, descend = 0):
        """add : base value of increase
        style_weights:
            climb = 0
            top = 0
            walk = 0
            descend = 0
            return self.build_probability increase"""
        a = self.build_probability
        if self.climb_style == 'climb':
            self.build_probability += climb * add
        elif self.climb_style == 'top':
            self.build_probability += top * add
        elif self.climb_style == 'walk':
            self.build_probability += walk * add
        elif self.climb_style == 'descend':
            self.build_probability += descend * add
        b = self.build_probability
        return b - a
    
    def get_chances_by_density(
            self, 
            pheromone_layer,       
            build_if_over = 0,
            build_if_below = 5,
            erase_if_over = 27,
            erase_if_below = 0,
            build_strength = 1):
        """
        returns build_chance, erase_chance
        if layer nb value sum is between 
        """
        v = self.get_nb_26_cell_values(pheromone_layer, self.pose)
        v = np.sum(v)
        # v = self.scan_neighborhood_values(pheromone_layer.array, radius, self.pose, format_values=0)

        
        if build_if_over < v < build_if_below:
            build_chance = build_strength
        else:
            build_chance = 0
        if erase_if_over < v < erase_if_below:
            erase_chance = 0
        else:
            erase_chance = build_strength
        
        return build_chance, erase_chance

    def get_chance_by_relative_position(
            self,
            layer,
            build_below = -1,
            build_aside = -1,
            build_above = 1,
            build_strength = 1):
        b, s, t = self.analyze_relative_position(layer)
        build_chance = (build_below * b + build_aside * s + build_above * t) * build_strength
        return build_chance
    
    def get_chance_by_climb_style(
            self, 
            climb = 0.5,
            top = 2,
            walk = 0.1,
            descend = -0.05,
            chance_weight = 1):
        "chance is returned based on the direction values and chance_weight"

        last_moves = self.move_history[-3:]
        if last_moves == ['up', 'up', 'up']:
            # climb_style = 'climb'
            build_chance = climb
        elif last_moves == ['up', 'up', 'side']:
            # climb_style = 'top'
            build_chance = top
        elif last_moves == ['side', 'side', 'side']:
            # climb_style = 'walk' 
            build_chance = walk
        elif last_moves == ['down', 'down', 'down']:
            # climb_style = 'descend' 
            build_chance = descend
        else:
            build_chance = 0

        build_chance *= chance_weight

        return build_chance


    def build(self, layer, pose = None):
        # if pose == None:
        #     pose = self.pose
        # else: 
        #     pass
        # if n != 0:
        #     self.pose = np.mod(self.pose, np.asarray([n,n,n]))
        try:
            set_value_at_index(layer, self.pose, 1)
            bool_ = True
        except Exception as e:
            print(e)
            print('cant build here:', self.pose)
            bool_ = False
        return bool_
    
    def erase(self, layer, only_face_nb = True, reintroduce = False):
        """erase from layer
        no reintroduction"""
        if only_face_nb:
            v = self.get_nb_6_cell_values(layer, self.pose, reintroduce)
            mask = self.get_erase_mask_6(layer, reintroduce)
            v[mask] = -1
            places = self.get_nb_6_cell_indicies(self.pose, reintroduce)
            places = np.asarray(places)
            choice = np.argmax(v)
            place = places[choice]    
        else:
            v = self.get_nb_26_cell_values(layer)
            mask = self.get_erase_mask_26(layer, reintroduce)
            v[mask] = -1
            choice = np.argmax(v)
            cube = self.get_nb_26_cell_indicies(self.pose, reintroduce)

            vector = cube[choice]
            place = self.pose + vector
       
        try:
            set_value_at_index(layer, place, 0)
            bool_ = True
        except Exception as e:
            print(e)
            print('cant erase this:', place)
            print(places)
            print(choice)
            print(v)
            x,y,z = place
            a = self.ground_layer.array[x][y][z]
            print(a)
            
            bool_ = False
        return bool_

    def check_offset(self, offset_layer):
        """        return ground directions as bools"""
        # get nb cell indicies
        nbs_values = self.get_nb_cell_values(offset_layer, self.pose)
        exclude_pheromones = np.logical_not(nbs_values == 0)
        return exclude_pheromones
    
    def check_build_conditions(self, layer, only_face_nbs = True):
        if only_face_nbs:
            v = self.get_nb_6_cell_values(layer, self.pose)
            if np.sum(v) > 0:
                return True
        else:
            if 0 < get_sub_array(layer, 1, self.pose, format_values = 0):
                return True
        return False
    

    def work(self, build_chance, erase_chance, ground, clay_moisture_layer, go_home_after_build, reach_to_build, reach_to_erase, stacked_chances = True):
        """build or erase a ground voxel based on the combined chance outputs of different chance_analyses
    returns built_bool, erased_bool
        """
        if stacked_chances:
            self.build_chance += build_chance
            self.erase_chance += erase_chance
        else:
            self.build_chance = build_chance
            self.erase_chance = erase_chance
        # CHECK IF BUILD CONDITIONS are favorable
        build_condition = self.check_build_conditions(ground)
        if self.build_chance >= reach_to_build and build_condition == True:
            built = self.build(ground)
            self.build(clay_moisture_layer)
            if built and go_home_after_build:
                self.reset_bool = True
                clay_moisture_layer.decay_linear()
        elif self.erase_chance >= reach_to_erase and build_condition == True:
            erased = self.erase(ground)
            self.erase(clay_moisture_layer)
        return built, erased


direction_dict_np = {
    'up' : np.asarray([0,0,1]),
    'front' : np.asarray([0,-1,0]),
    'right' : np.asarray([1,0,0]),
    'back' : np.asarray([0,1,0]),
    'left' : np.asarray([-1,0,0]),
    'down' : np.asarray([0,0,-1]),
}
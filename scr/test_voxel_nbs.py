import numpy as np
# import show_voxel_plt as show
# from voxel_builder_library import direction_dict_np

# def value_at_index(array, index = [0,0,0], value = 1):
#     i,j,k = index
#     array[i][j][k] = value
#     return array

# def get_color_array(array, n):
#     a = np.copy(array)
#     b = a.reshape([n,n,n,1])
#     b = 1 - b
#     colors = np.concatenate([b,b,b], axis = -1)
#     return colors

# # array
# n = 3
# a = np.zeros(n ** 3)
# a = a.reshape(n,n,n)

# # init pose
# pose = [1,1,1]
# a = value_at_index(a, pose, 1)

# # move
# direction =     'up'
# direction =     'down' 
# direction =     'left' 
# direction =     'right' 
# direction =     'front' 
# direction =     'back'
# d_vector = direction_dict_np[direction]

# pose_vector = np.asarray(pose)
# new_pose = pose_vector + d_vector
# print(new_pose)

# a = value_at_index(a, new_pose, 0.5)
# # show
# fig, ax = show.init_fig()
# colors = get_color_array(a, n)

# show.show_voxel(fig, ax, a, colors)

# bool_ = np.array([True, True, False, False, False])
# checklist = np.arange(5)
# checklist[bool_] = 0
# print(checklist)
test_i = np.indices((4,4,4))
x_min = 2
x_max = 2
z_max = 1
# x1 = np.logical_not(test_i[0,:,:,:] < x_min)
# x2 =np.logical_not(test_i[1,:,:,:] > x_max)
# z = np.logical_not(test_i[2,:,:,:] > z_max)

x1 = test_i[2,:,:,:] >= x_min
x2 = test_i[2,:,:,:] <= x_max
z = test_i[0,:,:,:] <= z_max


# x = np.logical_and(x1, x2, z)
# x = np.where(z == True, 1, 0)
d = np.zeros((4,4,4))
d[x2 & x1 & z] = 1
print('x', d)







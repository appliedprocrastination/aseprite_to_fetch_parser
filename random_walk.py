import numpy as np
import copy as cp

from parser import numpy_to_fetch

num_x = 19
num_y = 10
animation_length = 20
animation = []
frame_1 = np.zeros((num_x, num_y))
x_start = 10#np.random.randint(low=0,high=num_x)
y_start = 1#np.random.randint(low=0,high=num_y)
frame_1[x_start, y_start] = 1
animation.append(frame_1)
print(frame_1)
def walk_once(animation):
    cur_frame = cp.deepcopy(animation[-1])
    x_max, y_max = cur_frame.shape
    x_pos, y_pos = np.where(cur_frame == 1)
    x_pos = x_pos[0]; y_pos = y_pos[0]

    next_frame = np.zeros((x_max, y_max))
    moved = False
    print(x_pos, y_pos)
    while not moved:
        diraction = np.random.randint(low=0, high=4)
        print(diraction)
        if diraction == 0 and (y_pos < y_max-2):
            y_pos += 1
            moved = True
        elif diraction == 1 and (x_pos < x_max-2):
            x_pos += 1
            moved = True
        elif diraction == 2 and (y_pos > 1):
            y_pos -= 1
            moved = True
        elif diraction == 3 and (x_pos > 1):
            x_pos -= 1
            moved = True
    print(x_pos, y_pos)
    next_frame[x_pos, y_pos] = 1
    animation.append(cur_frame + next_frame)
    animation.append(next_frame)

    print(cur_frame)
    print(next_frame)

for i in range(animation_length):
    walk_once(animation)
print("asdasdasdasdasdasdas")
for i in range(len(animation)):
    animation[i] = np.flip(animation[i], 1)
print(animation[0].transpose())

numpy_to_fetch(animation)
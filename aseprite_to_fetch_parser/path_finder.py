from parser import *

import numpy as np

def number_of_active_pixels(frame):
    boolean_matrix = np.where(frame > 0, 1, 0)
    return  np.sum(boolean_matrix)

def draw_frame(frame):
    anim = []
    for i in range(len(frame[1,:])):
        anim = draw_row(frame, i)
        print(anim)
    return anim

def draw_row(frame, row_index):
    col_index = np.where(frame[row_index] > 0)
    anim = []
    for i in col_index:
        print("Here", i)
        anim = lift_one_column(frame, i, row_index)
    #print(anim)
    return anim

def lift_one_column(frame, x, y):
    animation = []
    for i in range(y+1):
        print(i)
        blank_frame = np.copy(frame) * 0
        blank_frame[x, i] = 20
        blank_frame = np.flip(blank_frame)
        if i > 0:
            animation.append(blank_frame + animation[i-1])
        #print(blank_frame)
        animation.append(blank_frame)
    #print(animation)
    return animation


if __name__ == "__main__":
    test_frame = aseprite_to_numpy("test_frame.aseprite")[0]
    print(test_frame)
    anim = draw_frame(test_frame)
    #print(anim)
    #show_animation(anim)
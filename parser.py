from aseprite import AsepriteFile

import matplotlib.animation as plt_animation
import matplotlib.pyplot as plt
import numpy as np
import copy as cp
import binascii
import glob
import os

#Just for more suitable formating when printing the numpy arrays
np.set_printoptions(edgeitems=3,infstr='inf',
                    linewidth=75, nanstr='nan', precision=8,
                    suppress=False, threshold=1000, formatter=None)

def aseprite_to_numpy(file_path):
    # Read file using py_aseprite
    with open(file_path, "rb") as f:
        a = f.read()
        parsed_file = AsepriteFile(a)
        frames = parsed_file.frames
        header = parsed_file.header

    #Check sice of color values
    if header.color_depth == 8:
        color_size = 2
    elif header.color_depth == 16:
        color_size = 4
    else:
        raise ValueError("Unknown color depth: {}".format(header.color_depth))

    #Check if there are used multiple layers
    if frames[0].num_chunks == 4:
        layers = False
    elif frames[0].num_chunks >= 6:
        layers = True
    else:
        raise ValueError("Unkonwn number of chunks in first frame: {}".format(frames[0].num_chunks))
    
    width, height = header.width, header.height
    animation = []
    new_frame = False
    frame = None
    for i, frame in enumerate(frames):
        for chunk in frame.chunks:
            # Only insterested in the chunks containing the data
            if chunk.chunk_type == 0x2005:
                # Make sure to use the right layer index dependent on wether multiple layers are used or not
                if (layers and chunk.layer_index) or (not layers and chunk.layer_index == 0):
                    if not new_frame:
                        frame = np.zeros((width, height))
                        new_frame = True
                    chunk_width, chunk_height = int(chunk.data["width"]), int(chunk.data["height"])
                    data = binascii.hexlify(chunk.data["data"])
                    cnt_x = chunk.x_pos
                    cnt_y = chunk.y_pos
                    for i in range(chunk_width * chunk_height):
                        #Wors way ever to convert from bytes to int...
                        val = data[i*color_size:i*color_size+color_size]
                        val = val[0:2]
                        val_str = "{}".format(val)[1:]
                        val_int = int(val, 16)
                        #If grayscale are used, flip the scale
                        if color_size == 4:
                            val_int = 255 - val_int
                        if val_int > 0:
                            frame[cnt_x, cnt_y] = val_int
                        cnt_x += 1
                        if cnt_x == chunk_width + chunk.x_pos:
                            cnt_x  = chunk.x_pos
                            cnt_y += 1
        if new_frame:   
            animation.append(frame)
            new_frame = False

    return animation

def numpy_to_fetch(animation, outfile="out", scale_from=1, scale_to=1):
    # Converts a list of numpy arrays to a fetch compatible animations and saves it to file
    num_frames = len(animation)
    num_x, num_y = animation[0].shape
    pwm_frames = []
    with open("{}_D.bin".format(outfile), "wb") as fp:
        for i in range(num_frames):
            #Dont want to change original frame, better safe then sorry
            frame = cp.deepcopy(animation[i])

            #Turn the matrix the rigt way
            frame = frame.transpose()
            frame = np.flip(frame, 0)

            #Convet every row to a 32 bit number
            binary_factors = 2**np.linspace(0,num_y, num_y+1)[0:-1]
            binary_frame_matrix = (frame > 0)
            binary_frame_array = np.sum(binary_frame_matrix * binary_factors.reshape(-1,1), 0)
            binary_frame_array_uint32 = np.uint32(binary_frame_array.astype(int))
    
            #Sets every zero to 20 as the unactive magnets should have a even state
            #frame[frame == 0] = 20

            frame = (frame / np.max(frame)) * 4096
            #If svaling are set, this will take care of it
            pwm_frame_uint16 = np.uint16(frame)# * scale_to / scale_from
            
            #fp.write(bytes(binary_frame_array_uint32))
            pwm_frames.append(pwm_frame_uint16)
    
        for pwm_frame in pwm_frames:
            fp.write(bytes(pwm_frame))

    #Creates the config file
    with open("{}_C.txt".format(outfile), "w") as fp:
        fp.write("{},{},{},0,0,1,0,-1,0,-1,0".format(num_x, num_y, num_frames))


def motion_blur(animation, upsampling=4, fade_min=8, max_value=20):
    # Adds fading between two frames
    out_animation = []
    for idx in range(len(animation)-1):
        current_frame = np.copy(animation[idx])

        next_frame = np.copy(animation[idx+1])

        fading_idx = np.logical_xor(np.logical_and(current_frame, next_frame), current_frame)
        out_animation.append(current_frame)
        if np.sum(fading_idx):
            for i in range(1, upsampling):
                fade_frame = np.copy(current_frame)
                fade_value = max_value - np.round((max_value - fade_min) / (upsampling - 1) * i) 
                fade_frame[fading_idx] = fade_value
                out_animation.append(fade_frame)

    return out_animation

def show_animation(animation, fps=4):
    # Simple illustration of the animation
    fig, ax = plt.subplots(1,1)
    img_animation = []
    for i, a in enumerate(animation):
        plt.title(f"Frame {len(animation)}/{i}")
        img = ax.imshow(a.transpose(), aspect='equal', vmax=20, vmin=0, cmap=plt.get_cmap("Greys"))
        img_animation.append([img])
    anim = plt_animation.ArtistAnimation(fig, img_animation, interval=round(1000/fps), blit=True)
    plt.show()


def append_animation(numpy_animation, num_repeat=20):
    # Extends the last frame in the animation
    last_frame = np.copy(numpy_animation[-1])
    for i in range(num_repeat):
        numpy_animation.append(last_frame)

    return numpy_animation
    
def take_down_animation(numpy_animation):
    # Generates the frames to gently take down the ferro fluid from the last frame in an animation
    last_frame = np.copy(numpy_animation[-1])
    highest_pxl_idx = 0
    row_mask = np.where(np.sum(last_frame, 1) > 0, 20, 0)

    for i in range(len(row_mask)-1):
        if row_mask[i] and row_mask[i+1]:
            row_mask[i+1] = 0

    height = len(last_frame[1,:])
    for i in range(height):
        if sum(last_frame[:,i]) > 0:
            highest_pxl_idx = i
            break

    fade_frame = None
    for i in range(highest_pxl_idx, len(last_frame[1,:])):
        fade_frame = np.copy(last_frame) * 0
        for j in range(i, len(last_frame[1,:])):
            fade_frame[:,j] = row_mask
        numpy_animation.append(fade_frame)

    return numpy_animation

def parse_and_save_to_file(filename, outfilename, append=10, take_down=True)
    # Just wrappes several of the functions above into one function
    animation_np = aseprite_to_numpy(filename)
    if append:
        animation_np = append_animation(animation_np, num_repeat=20)
    if take_down:
        animation_np = take_down_animation(animation_np)
    numpy_to_fetch(animation_np, outfile=outfilename)

def parse_folder(folder_path, start_number=100):
    # Parses all the .aseprite files in a given folder
    files = glob.glob(f"{folder_path}*.aseprite")
    print(files)
    for i, file_name in enumerate(files):
        parse_and_save_to_card(file_name, f"A{i+start_number}")

"""
----------------------------------
-- My system spesific functions --
----------------------------------
"""

# Default outfilepath are spesific for my computer (with antergos) for writing to SD card
def parse_and_save_to_card(filename, outfilename, outfilepath="/run/media/alphaos/3333-3438/", append=10, take_down=True):
    animation_np = aseprite_to_numpy(filename)
    if append:
        animation_np = append_animation(animation_np, num_repeat=20)
    if take_down:
        animation_np = take_down_animation(animation_np)
    numpy_to_fetch(animation_np, outfile=outfilepath+outfilename) #outfile="/mnt/usb/""+

# Also default from my computer
def unmount_card():
    os.system("umount /dev/mmcblk0p1")

if __name__ == "__main__":
    # Example 
    parse_and_save_to_file("example.aseprite", "fetch")
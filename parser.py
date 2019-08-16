from aseprite import AsepriteFile
import numpy as np
import copy as cp
import binascii
import struct
import zlib

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
        print("Frame:",i)
        for chunk in frame.chunks:
            # Only insterested in the chunks containing the data
            if chunk.chunk_type == 0x2005:
                print("Data Chunck!")
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
                        #Wors way ever to convert from byres to int...
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
    for i, a in enumerate(animation):
        print("Frame:",i)
        print(a)
        print()
        #print(np.flip(a.transpose()))
        #print()
    print(len(frames))
    print(len(animation))
    

    return animation

def numpy_to_fetch(animation, outfile="out", scale_from=1, scale_to=1):
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
            frame[frame == 0] = 20

            #If svaling are set, this will take care of it
            pwm_frame_uint8 = np.uint8(frame)# * scale_to / scale_from
            
            fp.write(bytes(binary_frame_array_uint32))
            pwm_frames.append(pwm_frame_uint8)
    
        for pwm_frame in pwm_frames:
            fp.write(bytes(pwm_frame))

    #Creates the config file
    with open("{}_C.txt".format(outfile), "w") as fp:
        fp.write("{},{},{},0,0,1,0,-1,0,-1,0".format(num_x, num_y, num_frames))

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Converts the aseprite file format to Fetch readable binary animation file.')
    import sys
    if len(sys.argv) < 3:
        print("No file ...")
    else:
        animation_np = aseprite_to_numpy(sys.argv[1])
        numpy_to_fetch(animation_np, outfile="/run/media/alphaos/3333-3438/"+sys.argv[2])
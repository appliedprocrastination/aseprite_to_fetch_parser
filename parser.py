from aseprite import AsepriteFile
import numpy as np
import binascii
import struct
import zlib
import copy as cp

def aseprite_to_numpy(file_path, scale_from=1, scale_to=1):
    animation = []
    with open(file_path, "rb") as f:
        a = f.read()
        parsed_file = AsepriteFile(a)
        frames = parsed_file.frames
        header = parsed_file.header

        layers = parsed_file.layers
        layer_tree = parsed_file.layer_tree
        
        for i, frame in enumerate(frames): 
            """
            print("Frame", i)
            for chunk in frame.chunks:
                #print(chunk.chunk_index)
                print(hex(chunk.chunk_type))
                if chunk.chunk_type == 0x2005:
                    #print(chunk.flags)
                    #print(chunk.layer_type)
                    #print(chunk.layer_child_level)
                    #print(chunk.default_width)
                    #print(chunk.default_height)
                    #print(chunk.blend_mode)
                    #print(chunk.opacity)
                    print(binascii.hexlify(chunk.data["data"]))
                    print()
                print()
            """
            for chunk in frame.chunks:
                #print(hex(chunk.chunk_type))
                if chunk.chunk_type == 0x2005:
                    #print(i, chunk.layer_index)
                    #if chunk.layer_index == 1:
                    frame = np.zeros((int(chunk.data["width"]), int(chunk.data["height"])), dtype="uint8")
                    data = binascii.hexlify(chunk.data["data"])#chunk.data["data"]
                    #print(data)
                    cnt_x = 0
                    cnt_y = 0
                    for i in range(int(chunk.data["width"]) * int(chunk.data["height"])):
                        val = data[i*4:i*4+4]
                        val = val[0:2]
                        val_str = "{}".format(val)[1:]
                        val_int = int(val, 16)
                        val_int = round((255 - val_int)*scale_to/scale_from)
                        frame[cnt_x, cnt_y] = val_int
                        cnt_x += 1
                        if cnt_x == chunk.data["width"]:
                            cnt_x  = 0
                            cnt_y += 1
                    animation.append(frame)
            
    return animation

def numpy_to_fetch(animation, outfile="out"):
    #global num_frames, num_x, num_y, animation
    num_frames = len(animation)
    num_x, num_y = animation[0].shape
    pwm_frames = []
    with open("{}.bin".format(outfile), "wb") as fp:
        for i in range(num_frames):
            frame = cp.deepcopy(animation[i])
            frame = frame.transpose()
            frame = np.flip(frame, 0)
            binary_factors = 2**np.linspace(0,num_y, num_y+1)[0:-1]
    
            binary_frame_matrix = (frame > 0)
            binary_frame_array = np.sum(binary_frame_matrix * binary_factors.reshape(-1,1), 0)
            binary_frame_array_uint32 = np.uint32(binary_frame_array.astype(int))
    
            frame[frame == 0] = 20
            pwm_frame_uint8 = np.uint8(frame)
            
            fp.write(bytes(binary_frame_array_uint32))
            pwm_frames.append(pwm_frame_uint8)
    
        for pwm_frame in pwm_frames:
            fp.write(bytes(pwm_frame))

    with open("{}.txt".format(outfile), "w") as fp:
        fp.write("{},{},{},0,0,1,0,-1,0,-1,0".format(num_x, num_y, num_frames))

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("No file path given...")
    else:
        animation_np = aseprite_to_numpy(sys.argv[1])
        numpy_to_fetch(animation_np)
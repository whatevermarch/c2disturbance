import bpy
import os.path
import random
import logging


#   number of samples (undistorted images)
N = 1

#   frame interval
frame_start = 1
frame_end = 5

#   sample file expression to be formatted later
sample_name = "{:03d}.png"

#   define sample directory and its name (expression)
sample_dir = bpy.path.abspath( '//../../data/samples' )

#   define output directory
output_dir = bpy.path.abspath( '//../../data/distorted' )

#   setup logging level
#logging.basicConfig( level=logging.DEBUG )


#   setup the environment before rendering
def init():

    logging.debug( "Initializing..." )
    logging.debug( "\tNumber of samples : {}".format( N ) )
    logging.debug( "\tRender from frame {} to frame {}".format( frame_start, frame_end ) )
    logging.debug( "\tRetreive samples from : {}".format( sample_dir ) )
    logging.debug( "\tSave outputs to : {}".format( output_dir ) )

    #   define animation frame range to be rendered
    bpy.context.scene.frame_start = frame_start
    bpy.context.scene.frame_end = frame_end
    
    #   set render device on scene settings
    bpy.context.scene.cycles.device = 'GPU'

    #   set rendering API
    cycles_pref = bpy.context.preferences.addons['cycles'].preferences
    for cdev_type in ('CUDA', 'OPENCL', 'NONE'):
        cycles_pref.compute_device_type = cdev_type
        if cycles_pref.has_active_device():
            break

    logging.debug( "\tRendering API : {}".format( cycles_pref.compute_device_type ) )
    logging.debug( "\tDevice(s) in use :" )
        
    #   enable appropriate devices
    #   for CUDA, use all available GPUs except host CPU
    if cycles_pref.compute_device_type == 'CUDA':
        for device in cycles_pref.devices:
            if device.type == 'CPU':
                device.use = False
            else:
                device.use = True
                logging.debug( "\t- {}".format( device.name ) )
            
    #   for OPENCL (usually a single-GPU system), enable both CPU and GPU 
    elif cycles_pref.compute_device_type == 'OPENCL':
        for device in cycles_pref.devices:
            device.use = True
            logging.debug( "\t- {}".format( device.name ) )

    logging.debug( "" )


#   render, ain't nothing else
def render():

    logging.debug( "Start rendering..." )
    
    #   define target texture node
    materials = bpy.data.materials
    tex_node = materials['Material.Text'].node_tree.nodes["Image Texture"]

    #   define image database in .blend file
    images = bpy.data.images

    #   define references to material nodes
    mat_water = bpy.data.materials['Material.Water']
    musgrave_1 = mat_water.node_tree.nodes["Musgrave Texture"]
    musgrave_2 = mat_water.node_tree.nodes["Musgrave Texture.001"]

    #   define scene to be rendered
    scene = bpy.data.scenes['Scene']

    #   loop all over the required samples
    for sample_idx in range(N):

        logging.debug( "Render sample [{} out of {}]".format( sample_idx, N ) )

        logging.debug( "\tloading texture..." )

        #   load new image
        new_img = images.load( os.path.join( sample_dir, sample_name.format( sample_idx ) ) )

        #   replace the existing image
        old_img = tex_node.image
        tex_node.image = new_img

        #   remove used image from the database to save memory space
        images.remove( old_img )

        logging.debug( "\tinitialize animation parameter..." )

        #   setup W-param for this sample
        #   randomize the initial values
        m1_start = random.uniform( 0.0, 50.0 )
        m1_end = m1_start + random.uniform( 20.0, 50.0 ) * ( -1 ) ** random.randint( 0, 1 )
        m2_start = random.uniform( 0.0, 50.0 )
        m2_end = m2_start + random.uniform( 20.0, 50.0 ) * ( -1 ) ** random.randint( 0, 1 )
        #   bound to keyframe
        bpy.context.scene.frame_set( frame_start )
        musgrave_1.inputs[1].default_value = m1_start
        musgrave_1.inputs[1].keyframe_insert( data_path="default_value" )
        musgrave_2.inputs[1].default_value = m2_start
        musgrave_2.inputs[1].keyframe_insert( data_path="default_value" )
        bpy.context.scene.frame_set( frame_end )
        musgrave_1.inputs[1].default_value = m1_end
        musgrave_1.inputs[1].keyframe_insert( data_path="default_value" )
        musgrave_2.inputs[1].default_value = m2_end
        musgrave_2.inputs[1].keyframe_insert( data_path="default_value" )

        logging.debug( "\trender..." )

        #   set the output subdirectory by sample index
        scene.render.filepath = os.path.join( output_dir, sample_idx, "" )

        #   render animation
        bpy.ops.render.render( animation=True, write_still=True )

        logging.debug( "Sample [{}] completed!".format( sample_idx ) )

    logging.debug( "" )


if __name__ == "__main__":
    init()
    render()

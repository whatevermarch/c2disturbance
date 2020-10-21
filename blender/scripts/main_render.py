import bpy
import os.path
import random
import logging
import time


#   number of samples (undistorted images)
sample_start = 0
sample_end = 1

#   frame interval
frame_start = 1
frame_end = 3

#   sample file expression to be formatted later
sample_name = "{:03d}.png"

#   define sample directory and its name (expression)
sample_dir = os.path.abspath( bpy.path.abspath( '//../../data/samples' ) )

#   define output directory
output_dir = os.path.abspath( bpy.path.abspath( '//../../data' ) )

#   setup logging level
logging.basicConfig( level=logging.DEBUG )


#   setup the environment before rendering
def init():

    print( "Initializing..." )
    logging.debug( "Target samples : {} -> {}".format( sample_start, sample_end ) )
    logging.debug( "Render frame {} -> {}".format( frame_start, frame_end ) )
    logging.debug( "Retrieve samples from : {}".format( sample_dir ) )
    logging.debug( "Save outputs to : {}".format( output_dir ) )

    #   define animation frame range to be rendered
    bpy.context.scene.frame_start = frame_start
    bpy.context.scene.frame_end = frame_end
    
    #   set render device on scene settings
    bpy.context.scene.cycles.device = 'GPU'

    #   retrieve all available devices
    cycles_pref = bpy.context.preferences.addons['cycles'].preferences
    cycles_pref.get_devices()

    #   set rendering API
    for cdev_type in ('CUDA', 'OPENCL', 'NONE'):
        cycles_pref.compute_device_type = cdev_type
        if cycles_pref.has_active_device():
            break

    logging.debug( "Rendering API : {}".format( cycles_pref.compute_device_type ) )
    logging.debug( "Device(s) in use :" )
        
    #   enable appropriate devices
    #   for CUDA, use all available GPUs except host CPU
    if cycles_pref.compute_device_type == 'CUDA':
        for device in cycles_pref.devices:
            if device.type == 'CPU':
                device.use = False
            else:
                device.use = True
                logging.debug( "\t{}".format( device.name ) )
            
    #   for OPENCL (usually a single-GPU system), enable both CPU and GPU 
    elif cycles_pref.compute_device_type == 'OPENCL':
        for device in cycles_pref.devices:
            device.use = True
            logging.debug( "\t{}".format( device.name ) )


#   render, ain't nothing else
def render():

    #   define target texture node
    materials = bpy.data.materials
    tex_node = materials['Material.Text'].node_tree.nodes["Image Texture"]

    #   define image database in .blend file
    images = bpy.data.images

    #   define references to material nodes
    mat_water = bpy.data.materials['Material.Water']
    node_musgrave_1 = mat_water.node_tree.nodes["Musgrave Texture"]
    node_musgrave_2 = mat_water.node_tree.nodes["Musgrave Texture.001"]
    node_mix = mat_water.node_tree.nodes["Mix"]
    node_out = mat_water.node_tree.nodes["Material Output"]

    #   define scene to be rendered
    scene = bpy.data.scenes['Scene']

    #   initialize performance timer
    num_samples = sample_end - sample_start + 1
    t_avg_per_sample = 0.0

    #   loop all over the required samples
    for sample_idx in range( sample_start, sample_end + 1 ):

        print( "Rendering sample [{} out of {}]...".format( sample_idx - sample_start + 1, num_samples ) )

        #   start the timer
        t_start = time.process_time()

        logging.debug( "loading texture..." )

        #   load new image
        new_img = images.load( os.path.join( sample_dir, sample_name.format( sample_idx ) ), check_existing=False )

        #   replace the existing image
        old_img = tex_node.image
        tex_node.image = new_img

        #   remove used image from the database to save memory space
        if old_img != None:
            images.remove( old_img )

        logging.debug( "initialize animation parameter..." )

        #   setup W-param for this sample
        #   randomize the initial values
        m1_start = random.uniform( 0.0, 50.0 )
        m1_end = m1_start + random.uniform( 32.0, 64.0 ) * ( -1 ) ** random.randint( 0, 1 )
        m2_start = random.uniform( 0.0, 50.0 )
        m2_end = m2_start + random.uniform( 32.0, 64.0 ) * ( -1 ) ** random.randint( 0, 1 )
        #   bound to keyframe
        bpy.context.scene.frame_set( 1 )
        node_musgrave_1.inputs[1].default_value = m1_start
        node_musgrave_1.inputs[1].keyframe_insert( data_path="default_value" )
        node_musgrave_2.inputs[1].default_value = m2_start
        node_musgrave_2.inputs[1].keyframe_insert( data_path="default_value" )
        bpy.context.scene.frame_set( 100 )
        node_musgrave_1.inputs[1].default_value = m1_end
        node_musgrave_1.inputs[1].keyframe_insert( data_path="default_value" )
        node_musgrave_2.inputs[1].default_value = m2_end
        node_musgrave_2.inputs[1].keyframe_insert( data_path="default_value" )

        logging.debug( "\tMusgrave[0] : {} -> {} ".format( m1_start, m1_end ) )
        logging.debug( "\tMusgrave[1] : {} -> {} ".format( m2_start, m2_end ) )

        logging.debug( "render..." )

        #   render undistorted version first
        #   unlink musgrave texture (displacement controller)
        if node_mix.outputs[0].is_linked:
            mat_water.node_tree.links.remove( node_mix.outputs[0].links[0] )

        #   set the output subdirectory by sample index
        scene.render.filepath = os.path.join( output_dir, "undistorted", str( sample_idx ) )

        #   render single frame
        bpy.ops.render.render( write_still=True )
        
        #   then render distorted version
        #   relink musgrave texture
        mat_water.node_tree.links.new( node_mix.outputs[0], node_out.inputs[2] )

        #   set the output subdirectory by sample index
        scene.render.filepath = os.path.join( output_dir, "distorted", str( sample_idx ), "###" )

        #   render animation
        bpy.ops.render.render( animation=True, write_still=True )

        #   stop the timer, and calculate exec. time per sample
        t_end = time.process_time()
        t_diff = t_end - t_start
        t_avg_per_sample += t_diff / num_samples

        print( "Sample [{}] completed! with {} s.".format( sample_idx, t_diff ) )

    print( "Rendering completed! with average {} seconds per sample.".format( t_avg_per_sample ) )


if __name__ == "__main__":
    init()
    render()

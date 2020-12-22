import bpy

import sys
import os.path
import logging
import time
import argparse

#   import custom modules
device = bpy.data.texts.load( bpy.path.abspath( "//scripts/device.py" ) ).as_module()
anim = bpy.data.texts.load( bpy.path.abspath( "//scripts/anim.py" ) ).as_module()

#   sample file expression to be formatted later
sample_name_format = "{:04d}"
sample_name_ext = ".jpg"

#   setup logging level
#logging.basicConfig( level=logging.DEBUG )


#   substitute texture by the new one with corresponding sample index
def change_texture( node_texture, s_dir, s_idx ):

    #   define image database in .blend file
    db_img = bpy.data.images

    #   load new image
    new_img = db_img.load( os.path.join( s_dir, sample_name_format.format( s_idx ) + sample_name_ext ), check_existing=False )

    #   replace the existing image
    old_img = node_texture.image
    node_texture.image = new_img

    #   remove used image from the database to save memory space
    if old_img != None:
        db_img.remove( old_img )

#   render UNDISTORTED version
def render_undistorted( scene, s_idx, o_dir ):

    #   set the output subdirectory by sample index
    scene.render.filepath = os.path.join( o_dir, "undistorted", sample_name_format.format( s_idx ) )

    #   render single frame
    bpy.ops.render.render( write_still=True )

#   render DISTORTED version
def render_distorted( scene, s_idx, o_dir ):

    #   set the output subdirectory by sample index
    scene.render.filepath = os.path.join( o_dir, "distorted", sample_name_format.format( s_idx ), "####" )

    #   render animation
    bpy.ops.render.render( animation=True, write_still=True )

#   setup the environment before rendering
def init( f_start, f_end, gpu_id ):

    print( ">>>>>\tStart initializing" )

    #   define animation frame range to be rendered
    anim.set_target_frame( f_start, f_end )

    #   set render device on scene settings
    device.customize( gpu_id )

#   render, ain't nothing else
def render( s_start, s_end, s_dir, o_dir, wave_scale, amplifier ):

    assert s_start <= s_end, "First sample is not followed by last sample."
    assert s_start >= 0, "First sample index cannot be lower than 0."

    print( ">>>>>\tStart rendering" )

    #   define references to material nodes
    materials = bpy.data.materials
    node_tex = materials['Material.Text'].node_tree.nodes["Image Texture"]
    mat_water = materials['Material.Water']
    node_musgrave_c = mat_water.node_tree.nodes["Musgrave.Coarse"]
    node_musgrave_f = mat_water.node_tree.nodes["Musgrave.Fine"]
    node_amplifier = mat_water.node_tree.nodes["Amplifier"]
    node_out = mat_water.node_tree.nodes["Material Output"]

    #   define scene to be rendered
    scene = bpy.data.scenes['Scene']

    #   initialize performance timer
    num_samples = s_end - s_start + 1
    t_avg_per_sample = 0.0

    logging.debug( "Render sample {} -> {}".format( s_start, s_end ) )
    logging.debug( "Retrieve samples from : {}".format( s_dir ) )

    #   loop all over the required samples
    for s_idx in range( s_start, s_end + 1 ):

        print( "Rendering sample [{} out of {}]...".format( s_idx - s_start + 1, num_samples ) )

        #   start the timer
        t_start = time.process_time()

        logging.debug( "Loading texture..." )

        #   load new image
        change_texture( node_tex, s_dir, s_idx )

        logging.debug( "Initialize animation parameter..." )

        #   setup material parameters
        anim.set_param_musgrave( node_musgrave_c, node_musgrave_f, wave_scale )
        anim.set_param_amplifier( node_amplifier, amplifier )

        logging.debug( "Render..." )

        #   unlink musgrave texture (displacement controller)
        if node_amplifier.outputs[0].is_linked:
            mat_water.node_tree.links.remove( node_amplifier.outputs[0].links[0] )

        #   render undistorted version first
        render_undistorted( scene, s_idx, o_dir )

        #   relink musgrave texture
        mat_water.node_tree.links.new( node_amplifier.outputs[0], node_out.inputs[2] )

        #   then render distorted version
        render_distorted( scene, s_idx, o_dir )

        #   stop the timer, and calculate exec. time per sample
        t_end = time.process_time()
        t_diff = t_end - t_start
        t_avg_per_sample += t_diff / num_samples

        print( "Sample [{}] completed! with {} s.".format( s_idx, t_diff ) )

    print( "Rendering completed! with average {} seconds per sample.".format( t_avg_per_sample ) )

    logging.debug( "Results available at : {}".format( o_dir ) )


if __name__ == "__main__":

    parser = argparse.ArgumentParser( description=\
        'This script is to generate distortion on many image samples to feed to ML model afterwards.' )
    
    parser.add_argument( '--frames', type=int, nargs=2, default=[ 1, 3 ],
            help='target frame range [first last], default is 1 -> 3.' )   
    parser.add_argument( '--samples', type=int, nargs=2, default=[ 0, 1 ],
            help='sample index range [first last], default is 0 -> 1.' )
    parser.add_argument( '--sample_dir', type=str, default='../../data/samples',
            help='directory containing sample images (with format ###.png), default is ../../data/samples.' )
    parser.add_argument( '--wave_scale', type=float, default=0.0,
            help='scale of wave that distort the view. recommended values are between 3.2 - 8.0. \
                    this will be applied to **ALL** samples. if you are not certain, \
                    leave this parameter to let the script properly randomize for **EACH** sample.' )
    parser.add_argument( '--amplifier', type=float, default=0.0,
            help='distortion amplifier. recommended values are between 0.135 - 0.572. \
                    this will be applied to **ALL** samples. if you are not certain, \
                    leave this parameter to let the script properly randomize for **EACH** sample.' )
    parser.add_argument( '--gpu_id', type=int, default=-1,
            help='(CUDA only) gpu id to be used (will use this gpu only), use all that is available if not specified. \
                    No effect on non-NVIDIA system' )
    parser.add_argument( '--output_dir', type=str, default='../../data',
            help='directory to place output images (in distorted/undistorted directories), default is ../../data.' )

    if '--' in sys.argv:
        args = parser.parse_args( sys.argv[sys.argv.index('--') + 1:] )
    else:
        args = parser.parse_args( [] )

    frame_start, frame_end = args.frames
    sample_start, sample_end = args.samples
    sample_dir = os.path.abspath( bpy.path.abspath( '//' + args.sample_dir ) )
    wave_scale = args.wave_scale
    amplifier = args.amplifier
    gpu_id = args.gpu_id
    output_dir = os.path.abspath( bpy.path.abspath( '//' + args.output_dir ) )

    init( frame_start, frame_end, gpu_id )
    render( sample_start, sample_end, sample_dir, output_dir, wave_scale, amplifier )

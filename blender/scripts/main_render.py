import bpy
import os.path
import logging
import time
import argparse

import device
import anim


#   sample file expression to be formatted later
sample_name = "{:03d}.png"

#   setup logging level
logging.basicConfig( level=logging.DEBUG )


#   substitute texture by the new one with corresponding sample index
def change_texture( db_img, node_texture, s_dir, s_idx ):

    #   load new image
    new_img = db_img.load( os.path.join( s_dir, sample_name.format( s_idx ) ), check_existing=False )

    #   replace the existing image
    old_img = node_texture.image
    node_texture.image = new_img

    #   remove used image from the database to save memory space
    if old_img != None:
        db_img.remove( old_img )


#   setup the environment before rendering
def init( f_start, f_end ):

    print( ">>>>>\tStart initializing\t>>>>>" )

    #   define animation frame range to be rendered
    anim.set_target_frame( f_start, f_end )
    
    #   set render device on scene settings
    device.customize()


#   render, ain't nothing else
def render( s_start, s_end, s_dir, o_dir ):

    print( ">>>>>\tStart rendering\t>>>>>" )

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
        change_texture( images, tex_node, s_dir, s_idx )

        logging.debug( "Initialize animation parameter..." )

        #   setup W-param for this sample
        anim.setup_keyframe_musgrave( node_musgrave_1, node_musgrave_2 )

        logging.debug( "Render..." )

        #   render undistorted version first
        #   unlink musgrave texture (displacement controller)
        if node_mix.outputs[0].is_linked:
            mat_water.node_tree.links.remove( node_mix.outputs[0].links[0] )

        #   set the output subdirectory by sample index
        scene.render.filepath = os.path.join( o_dir, "undistorted", str( s_idx ) )

        #   render single frame
        bpy.ops.render.render( write_still=True )
        
        #   then render distorted version
        #   relink musgrave texture
        mat_water.node_tree.links.new( node_mix.outputs[0], node_out.inputs[2] )

        #   set the output subdirectory by sample index
        scene.render.filepath = os.path.join( o_dir, "distorted", str( s_idx ), "###" )

        #   render animation
        bpy.ops.render.render( animation=True, write_still=True )

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

    parser.add_argument( '--sample_dir', type=str, default='../../data/samples',
            help='directory containing sample images (with format ###.png), default is ../../data/samples' )
    parser.add_argument( '--output_dir', type=str, default='../../data',
            help='directory to place output images (in distorted/undistorted directories), default is ../../data' )
    parser.add_argument( '--samples', type=int, nargs=2, default=[ 0, 1 ],
            help='sample index range [first last], default is 0 -> 1' )
    parser.add_argument( '--frames', type=int, nargs=2, default=[ 1, 3 ],
            help='target frame range [first last], default is 1 -> 3' )

    args = parser.parse_args()
    frame_start, frame_end = args.frames
    sample_start, sample_end = args.samples
    sample_dir = os.path.abspath( bpy.path.abspath( '//' + args.sample_dir ) )
    output_dir = os.path.abspath( bpy.path.abspath( '//' + args.output_dir ) )

    init( frame_start, frame_end )
    render( sample_start, sample_end, sample_dir, output_dir )

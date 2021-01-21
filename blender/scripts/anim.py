import bpy
import random
import logging

#   set the minimum and maximum offset of W-value
w_init_min = -50.0
w_init_max = 50.0
w_offset_min = 1.5
w_offset_max = 2.8

#   set the range of scale for coarse wave
scale_c_min = 3.2
scale_c_max = 8.0

#   set the range of appropriate amplifier factor
amp_min = 0.17
amp_max = 0.56


#   define animation frame range to be rendered
def set_target_frame( f_start, f_end ):

    assert f_start <= f_end, "First frame is not followed by last frame."
    assert f_start >= 1, "First frame cannot be lower than 1."
    assert f_end <= 100, "Last frame cannot exceed 100."

    logging.debug( "Render frame {} -> {}".format( f_start, f_end ) )

    bpy.context.scene.frame_start = f_start
    bpy.context.scene.frame_end = f_end

#   setup keyframe parameters FOR musgrave texture nodes
def set_param_musgrave( node_c, node_f, wave_scale=0.0 ):
        
    #   random W-param for this sample
    m1_start = random.uniform( w_init_min, w_init_max )
    m1_end = m1_start + random.uniform( w_offset_min, w_offset_max ) * ( -1 ) ** random.randint( 0, 1 )
    m2_start = random.uniform( w_init_min, w_init_max )
    m2_end = m2_start + random.uniform( w_offset_min, w_offset_max ) * ( -1 ) ** random.randint( 0, 1 )

    #   bound to keyframe
    bpy.context.scene.frame_set( 1 )
    node_c.inputs[1].default_value = m1_start
    node_c.inputs[1].keyframe_insert( data_path="default_value" )
    node_f.inputs[1].default_value = m2_start
    node_f.inputs[1].keyframe_insert( data_path="default_value" )
    bpy.context.scene.frame_set( 100 )
    node_c.inputs[1].default_value = m1_end
    node_c.inputs[1].keyframe_insert( data_path="default_value" )
    node_f.inputs[1].default_value = m2_end
    node_f.inputs[1].keyframe_insert( data_path="default_value" )

    #   reset target frame number
    bpy.context.scene.frame_set( 1 )

    logging.debug( "\tMusgrave[0].W : {:.4f} -> {:.4f}".format( m1_start, m1_end ) )
    logging.debug( "\tMusgrave[1].W : {:.4f} -> {:.4f}".format( m2_start, m2_end ) )

    #   control scale param
    scale_c = random.uniform( scale_c_min, scale_c_max ) if wave_scale == 0.0 else wave_scale
    scale_offset = ( scale_c_max - scale_c ) / ( scale_c_max - scale_c_min ) * 0.8 + 2.7
    scale_f = random.gauss( scale_c + scale_offset, 0.25 ) #  approx. by chebyshev's inequality
    node_c.inputs[2].default_value = scale_c
    node_f.inputs[2].default_value = scale_f

    logging.debug( "\tMusgrave[0].Scale : {:.4f}".format( scale_c ) )
    logging.debug( "\tMusgrave[1].Scale : {:.4f}".format( scale_f ) )

#   setup ampifier factor for the amount of distortion
def set_param_amplifier( node, factor=0.0 ):

    #   control amplifier param
    amp_factor = random.uniform( amp_min, amp_max ) if factor == 0.0 else factor
    node.inputs[1].default_value = amp_factor

    logging.debug( "\tAmplifier.Value : {:.4f}".format( amp_factor ) )

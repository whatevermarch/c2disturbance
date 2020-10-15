import bpy

#   define references to material nodes
mat_water = bpy.data.materials['Material.Water']
musgrave_1 = mat_water.node_tree.nodes["Musgrave Texture"]
musgrave_2 = mat_water.node_tree.nodes["Musgrave Texture.001"]

#   edit keyframe value
musgrave_1.inputs[1].default_value = 10.0
musgrave_1.inputs[1].keyframe_insert( data_path = "default_value" )

#   manage frame
curr_frame = bpy.context.scene.frame_current
bpy.context.scene.frame_set( curr_frame + 1 )
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 100
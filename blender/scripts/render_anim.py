import bpy

#   define sample index
N = 0

#   saved output directory
out_dir = bpy.path.abspath( '//../../data/distorted/{}/'.format(N) )

#   render with animation
scene = bpy.data.scenes['Scene']
scene.render.filepath = out_dir
bpy.ops.render.render( animation=True, write_still=True )

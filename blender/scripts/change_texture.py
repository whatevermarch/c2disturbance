import bpy
import os.path

#   number of samples (undistorted images)
N = 100

#   sample file expression to be formatted later
img_name = "{:03d}.png"

#   define sample directory and its name (expression)
img_dir = bpy.path.abspath( '//../../data/samples' )

#   define target texture node
materials = bpy.data.materials
tex_node = materials['Material.Text'].node_tree.nodes["Image Texture"]

#   define image database in .blend file
images = bpy.data.images

#   loop all over the required samples
for imgIdx in range(N):

    #   load new image
    new_img = images.load( os.path.join( img_dir, img_name.format( N ) ) )

    #   replace the existing image
    old_img = tex_node.image
    tex_node.image = new_img

    #   remove used image from the database to save memory space
    images.remove( old_img )

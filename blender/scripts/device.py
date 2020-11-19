import bpy
import logging

def customize():

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
    #   Note : should be only for AMD's integrated GPU (Ryzen APU)
    elif cycles_pref.compute_device_type == 'OPENCL':
        for device in cycles_pref.devices:
            device.use = True
            logging.debug( "\t{}".format( device.name ) )

import bpy

#   set render device on scene settings
bpy.data.scenes['Scene'].cycles.device = 'GPU'

#   set rendering API
cycles_pref = bpy.context.preferences.addons['cycles'].preferences
for cdev_type in ('CUDA', 'OPENCL', 'NONE'):
    try:
        cycles_pref.compute_device_type = cdev_type
        break
    except TypeError:
        pass
    
#   enable appropriate devices
#   for CUDA, use all available GPUs except host CPU
if cycles_pref.compute_device_type == 'CUDA':
    for device in cycles_pref.devices:
        if device.type == 'CPU':
            device.use = False
        else
            device.use = True
        
#   for OPENCL (usually a single-GPU system), enable both CPU and GPU 
elif cycles_pref.compute_device_type == 'OPENCL':
    for device in cycles_pref.devices:
        device.use = True

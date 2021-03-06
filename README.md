# Abstract
It is usually not too difficult to see an object through a turbulent surface such as
water and hot air; however, recognizing the object might be much harder, especially
for a computer that receives a digital image as an input. Therefore, we present an
approach to reconstruct the distorted image caused by refraction on the turbulent
surface using a stacked convolutional neural network cooperating with a generative
adversarial network. We also propose a simple but powerful computer graphics
model to simulate the turbulent refractive medium and generate distorted samples,
yielding unlimited training data for reinforcing the neural network. Even though an
undistorted result does not perfectly preserve the original object shape without the
disturbance, our machine learning model could reconstruct plausible geometry
information that is still recognizable as the object itself.

## Algorithm Sketch
![Capture](https://user-images.githubusercontent.com/52937810/121777436-506e4600-cb92-11eb-9eef-b8cf2243840e.PNG)

### Usage 

``` bash 
python ./run.py --total_images 4 --images_per_class 2 --frames_per_image 3

```

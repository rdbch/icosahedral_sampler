# Unwrapped Icosahedral Maps
Create unwrapped icosahedral maps from equirectangular images.


## Installation
This code was developed using ```python 3.8```, however it should run on anything that has  >= ```python 3.6```.

To install the requirements, one can simply run:

```bash
$ pip install -r requiremets.py
```

## Usage
The base class that one should use is:  

Additionally, one can check the provided [sample notebook](./examples.ipynb).

This repository also contains a command line utility program that can creates such a map: 
```bash
$ python unwrap.py --input=<path to input> \ 
                   --output=<path to output> \
                   --face_resolution=500 \ 
                   --face_offset=0
```
The second one, is by using the provided library as follows:

## TODOs
A list of TODOs that might be implemented in the future:
- [] add interpolation when asmpling the colors (current method: nearest)


## References
During the creation of this repository I hhave found the following articles to be useful:

- [http://www.paulbourke.net/panorama/icosahedral/](http://www.paulbourke.net/panorama/icosahedral/)
- [https://www.songho.ca/opengl/gl_sphere.html](https://www.songho.ca/opengl/gl_sphere.html)
- [https://en.wikipedia.org/wiki/Regular_icosahedron](https://en.wikipedia.org/wiki/Regular_icosahedron)
- [https://mathworld.wolfram.com/RegularIcosahedron.html](https://mathworld.wolfram.com/RegularIcosahedron.html)

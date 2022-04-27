import cv2
import numpy as np
from . import utils
from scipy.spatial.transform import Rotation as R


# ######################################################################################################################
#                                               ICOSAHEDRAL SAMPLER
# ######################################################################################################################
class IcosahedralSampler:
    def __init__(self, resolution: int = 500):
        """
        Create unwrapped icosahedral from equirectangular images. This class creates a 3D icosahedron as internal
        representation and is using it to sample the colors from an equirectangular image.

        Advantages of the representation:
            - faces have very little distorsion
            - can be subdivided (like a mesh) to creates faces (not yet in this repo :( )

        Arguments:s
              resolution: pixel resolution of a face

        References:
            - http://www.paulbourke.net/panorama/icosahedral/
            - https://en.wikipedia.org/wiki/Regular_icosahedron
            - https://mathworld.wolfram.com/RegularIcosahedron.html
        """

        self.resolution = resolution

        # unit sphere
        radius = 1.0
        self.vertices = self.get_vertices(radius)

        # faces - level 0
        self.faces = np.array([
             0,  1, 2,   0, 2, 3,   0, 3, 4,   0, 4, 5,   0, 5,  1,     # top    /\
             6,  1, 2,   7, 2, 3,   8, 3, 4,   9, 4, 5,  10, 5,  1,     # second \/
             1, 10, 6,   2, 6, 7,   3, 7, 8,   4, 8, 9,   5, 9, 10,     # third  /\
            11, 10, 6,  11, 6, 7,  11, 7, 8,  11, 8, 9,  11, 9, 10      # forth  \/
        ]).reshape(-1, 3)

    # =============================================== EDGE LENGTH ======================================================
    @property
    def edge_length(self) -> float:
        """
        Compute the icosahedron edge length in 3D (XYZ). Assumes that all edges have the same length.

        Returns:
            edge length (scalar)
        """
        return np.sqrt(np.sum((self.vertices[0] - self.vertices[1]) ** 2))

    # =============================================== GET VERTICES =====================================================
    def get_vertices(self, radius: float = 1.0) -> np.ndarray:
        """
        Return the list of vertices in 3D for the regular icosahedron of level 0. The iscosahedron has 12 vertices
        and it has been chosen to be aligned norm-south (aka the north and south pole are vertices).

        References:
        - https://en.wikipedia.org/wiki/Regular_icosahedron - see Spherical Coordinates section

        Args:
            radius: radius of the circumscribed sphere (default: 1.0)

        Returns:
            list of 3D vertices (having the length=radius)
        """
        # angles
        height       = np.arctan(1 / 2)  # 26.565 degree
        width_offset = np.deg2rad(36)
        unit_vector  = np.array([0, 0, 1])

        # top /\ - north pole
        vertices = [np.array([0, -1, 0])]

        # second \/ - first hexagon
        # third  /\ - second hexagon
        for i in range(0, 10):
            offset = 2 * (i % 5) + (i > 4)  #srry, overcomplicated way for treating the 2 hexa differently
            sign   = 1  - (i > 4) * 2
            rot_mat = R.from_euler('xy', [sign * height, offset * width_offset]).as_matrix().T
            vertices.append(unit_vector @ rot_mat)

        # forth \/ - south pole
        vertices.append(np.array([0, 1, 0]))

        # scale vertices
        vertices = np.array(vertices) # shape [12, 3]
        vertices /= np.linalg.norm(vertices, axis=-1, keepdims=True)
        vertices *= radius

        return vertices

    # =============================================== GET TRIANGLE COORDS ==============================================
    def __get_triangle_coords(self,
                              base_resolution: int,
                              is_up: bool,
                              center: bool = True,
                              normalize: bool = True,
                              homogeneous: bool = False ) -> np.ndarray:
        """
        Utility function that returns the coordinates of an equirectangular triangle that is drawn in a rectangular
        image. The triangle has as base either the top or the bottom edge.

        Args:
            base_resolution: edge length in pixels
            is_up: the triangle is facing up or down
            center: move the origin to be in the triangle's center of weight
            normalize: return normalized coordinates in interval [0, 1]
            homogeneous: return homogeneous points (add 1s on the last dimension)

        Returns:
            xy coordinates of the points lying inside the triangle
        """
        y = int(3 ** 0.5 / 2 * base_resolution)
        x = base_resolution
        triangle = np.array([[[x - 1, 0], [0, 0], [x // 2, y - 1]],
                             [[0, y - 1], [x - 1, y - 1], [x // 2, 0]]])

        # rasterize triangle (could also be done with analytically, but this is way more elegant)
        canvas = np.zeros([y, x], dtype=np.uint8)
        canvas = cv2.drawContours(canvas, [*triangle], int(is_up), color=1, thickness=-1)
        coords = np.argwhere(canvas == 1)[:, ::-1]

        # center coordinates in weight center
        if center:
            coords[..., 0] -= x // 2
            coords[..., 1] -= (1+is_up) * y // 3

        # normalize coordinates in interval [0, 1]
        if normalize:
            coords = coords / x

        # add homogeneous axis
        if homogeneous:
            ones = np.ones_like(coords[:, 0, None])
            coords = np.concatenate([coords, ones], axis=-1)

        return coords #[N, 2]

    # =============================================== GET FACE XYZ =====================================================
    def get_face_xyz(self, face_no: int) -> np.ndarray:
        """
        Method that generates the xyz coordinates of a face. These points can be later used to be projected onto the
        sphere and sample the color from the equirectangular image texture.

        Arguments:
            face_no: face number (0-11)
            res: resolution of the face (number of points of the base)

        Returns:
            coordinates in 3D of a given face of the icosahedron
        """
        vertex_xyz = self.vertices[self.faces[face_no]]

        # get face center in XYZ
        center = vertex_xyz.mean(axis=0)
        norm   = np.linalg.norm(center)
        center = center / norm

        # generate equilateral triangle and scale to edge length
        is_up = vertex_xyz[0, 1] < vertex_xyz[1, 1]
        xyz = self.__get_triangle_coords(self.resolution, is_up, normalize=True, homogeneous=True, center=True)
        xyz[:, :2] *= self.edge_length  # scale to edge length
        xyz[:, 2]  *= norm

        # rotate triangle to
        phi, theta = utils.xyz_2_polar(center)
        triangle_xyz = xyz @ R.from_euler('yx', [-phi, theta]).as_matrix()

        return triangle_xyz

    # =============================================== GET FACE RGB =====================================================
    def get_face_rgb(self, face_no, eq_image):
        """
        Utility method that uses the gnomonic projection to get rgb colors of a face given an equirectangular image.

        Arguments:
            face_no: face number to be returned
            eq_image: equirectangular image

        Returns:
            color sampled from equirectangular images [N, 3]
        """

        utils.check_eq_image_shape(eq_image)
        xyz = self.get_face_xyz(face_no)

        # raycast on sphere
        ray_xyz = xyz /  np.linalg.norm(xyz, axis=1, keepdims=True)

        # rotate to face center
        phi, theta = utils.xyz_2_polar(ray_xyz)
        x, y = utils.polar_2_equi(phi, theta, eq_image.shape)

        #TODO add interpolation
        return eq_image[y.astype(int), x.astype(int)]

    # =============================================== GET FACE IMAGE ===================================================
    def get_face_image(self, face_no, eq_image):
        """
        Project the plane of a face on the sphere and sample the colors. Retur

        Arguments:
            face_no: face number
            eq_image: equirectangular image to sample from

        Returns:
            RGB image of the face
        """

        utils.check_eq_image_shape(eq_image)
        colors = self.get_face_rgb(face_no, eq_image)

        # skew matrix build
        vertex_xyz = self.vertices[self.faces[face_no]]
        is_up = vertex_xyz[0, 1] < vertex_xyz[1, 1]
        xy = self.__get_triangle_coords(self.resolution, is_up, normalize=False, homogeneous=False, center=False)

        triangle_height = 3**0.5/2
        canvas = np.zeros([int(self.resolution*triangle_height), self.resolution, 3], dtype=np.uint8)
        canvas[xy[:, 1], xy[:, 0]] = colors
        return canvas

    # =============================================== UNWRAP ===========================================================
    def unwrap(self, eq_image, face_offset=0):
        """
        Project an equirectangular image onto an icosahedron and unwrapped it onta a plane surface. The resolution of
        the output images will be computed based on the resolution provided at the creation of the object.

        Arguments:
            eq_image: equirectangular image to be samples from
            face_offset: offset faces when creating the unwrapped image [-2, 2] (default: 0)

        Returns:
            unwrapped icosahedron with colors sampled from the equirectangular image.
        """

        # input check
        utils.check_eq_image_shape(eq_image)
        assert -2 <= face_offset <= 2, f'The face offset should be in the interval [-2, 2]. Current: {face_offset}'

        colors = [self.get_face_rgb(i, eq_image) for i in range(20)]
        h_res = int(3**0.5/2*self.resolution)
        canvas = np.ones([3*h_res, int(5.5*self.resolution), 3], dtype=np.uint8)*255

        # coordinates for moving the color from faces to canvas
        xy_up   = self.__get_triangle_coords(self.resolution, True, normalize=False, homogeneous=False, center=False)
        xy_down = self.__get_triangle_coords(self.resolution, False, normalize=False, homogeneous=False, center=False)

        loc_generator = [[l[0], (face_offset + 2 + l[1]) % 5] for l in enumerate(range(5))]

        # move colors from faces to canvas
        for num, loc in loc_generator:
            canvas[xy_up[..., 1],  int((loc+0.5)*self.resolution)+xy_up[..., 0]] = colors[num]
        for num, loc in loc_generator:
            canvas[h_res+xy_down[..., 1], int((loc+0.5)*self.resolution)+xy_down[..., 0]] = colors[5+num]
        for num, loc in loc_generator:
            canvas[h_res+xy_up[..., 1], loc*self.resolution+xy_up[..., 0]] = colors[10+num]
        for num, loc in loc_generator:
            canvas[2*h_res+xy_down[..., 1], loc*self.resolution+xy_down[..., 0]] = colors[15+num]

        return canvas


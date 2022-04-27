import os
import cv2
import argparse

from ico_sampler import IcosahedralSampler


args = argparse.ArgumentParser()
args.add_argument('-i', '--input', required=True, help="Path to the input image.")
args.add_argument('-o', '--output', required=True, help="Path to output.")
args.add_argument('-r', '--face_resolution', type=int, default=600, help="Resolution of a single triangular face.")
args.add_argument('-f', '--face_offset', type=int, default=0, help="Offset the way faces are arranges in the final image.")

if __name__ == '__main__':

    # handle inputs
    args = args.parse_args()
    image = cv2.imread(args.input)

    # unwrap image
    ico_sampler = IcosahedralSampler(resolution=args.face_resolution)
    unwrapped_image = ico_sampler.unwrap(image, face_offset=args.face_offset)

    # create output dir and save the unwrapped image
    output_dir = os.path.split(args.output)[0]
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    cv2.imwrite(args.output, unwrapped_image)

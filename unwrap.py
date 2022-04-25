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
    args = args.parse_args()

    image = cv2.imread(args.input)
    ico_sampler = IcosahedralSampler(resolution=args.face)
    unwrapped_image = ico_sampler.unwrap(image, face_offset=args.face_offset)

    output_dir = os.path.split(args.output)[0]
    if os.path.exists(output_dir):
        os.makedirs(output_dir)

    cv2.imwrite(args.output, unwrapped_image)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PIL import Image, ImageDraw
from obj import parse_obj, Obj, Face, Vec3
from dataclasses import dataclass
from typing import Dict, List
import argparse

DEFAULT_TEX_RES = 1024
DEFAULT_PEN_WIDTH = 1
DEFAULT_SUPER_SAMPLE = 1


@dataclass(frozen=True, eq=True)  # Make it hashable
class Edge:
    va: int
    vb: int
    uva: int
    uvb: int

    def __init__(self, va_idx: int, vb_idx: int, uva_idx: int, uvb_idx: int) -> None:
        # Ensure a is always the lower index, so that edges will be considered equal no matter in
        # what order the indices were specified.
        # Hack to initialize frozen variables.
        # https://stackoverflow.com/questions/57893902/how-can-i-set-an-attribute-in-a-frozen-dataclass-custom-init-method
        if va_idx < vb_idx:
            object.__setattr__(self, "va", va_idx)
            object.__setattr__(self, "vb", vb_idx)
            object.__setattr__(self, "uva", uva_idx)
            object.__setattr__(self, "uvb", uvb_idx)
        else:
            object.__setattr__(self, "va", vb_idx)
            object.__setattr__(self, "vb", va_idx)
            object.__setattr__(self, "uva", uvb_idx)
            object.__setattr__(self, "uvb", uva_idx)


def are_face_normals_equal(obj: Obj, faces: List[Face]) -> bool:
    normal: Vec3 = faces[0].normal(obj)
    for face in faces[1:]:
        if not normal.almostEquals(face.normal(obj)):
            return False

    return True


def filter_edges(obj: Obj, keep_support_edges: bool) -> List[Edge]:
    """Return unique edges. If clean_supports is true, filter all support edges."""
    neighbor_faces: Dict[Edge, List[Face]] = {}

    for face in obj.faces:
        for i in range(len(face.vertex_idxs)):
            next_i = (i + 1) % len(face.vertex_idxs)
            a = face.vertex_idxs[i]
            b = face.vertex_idxs[next_i]  # Wrap around to close the shape
            edge = Edge(a, b, face.uv_idxs[i], face.uv_idxs[next_i])
            neighbors: List[Face] = neighbor_faces.setdefault(edge, [])
            neighbors.append(face)

    edges_to_keep: List[Edge] = []
    num_skipped: int = 0

    if keep_support_edges:
        edges_to_keep = list(neighbor_faces.keys())
    else:
        for edge, faces in neighbor_faces.items():
            if len(faces) == 1 or not are_face_normals_equal(obj, faces):
                edges_to_keep.append(edge)
            else:
                num_skipped += 1

    print("Skipped edges: ", num_skipped)
    return edges_to_keep


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a clean wireframe for a given .obj model.")
    parser.add_argument("obj_file", help="Input obj file.")
    parser.add_argument("out_file", help="Output image file path.")
    parser.add_argument("--flipy", action="store_true", help="Flip Y UVs.")
    parser.add_argument("-r", "--resolution", type=int, default=DEFAULT_TEX_RES, help=f"Texture resolution. Default: {DEFAULT_TEX_RES}.")
    parser.add_argument("-w", "--width", type=int, default=DEFAULT_PEN_WIDTH, help=f"Line width. Default: {DEFAULT_PEN_WIDTH}.")
    parser.add_argument("-ss", "--supersample", type=int, default=DEFAULT_SUPER_SAMPLE, help=f"Use super-sampling to produce anti-aliased lines. A value <= 1 means no super-sampling (default). Default: {DEFAULT_SUPER_SAMPLE}")
    parser.add_argument("-a", "--all", action="store_true", help="Render all edges, don't remove support edges.")
    args = parser.parse_args()

    obj = parse_obj(args.obj_file, flip_uv_y=args.flipy)
    edges = filter_edges(obj, args.all)
    res = args.resolution
    ssres = max(1, args.supersample) * res
    w, h = ssres, ssres

    # Create grayscale texture
    with Image.new("L", (w, h), 0) as im:
        draw = ImageDraw.Draw(im)

        for edge in edges:
            uvs = (obj.uvs[edge.uva], obj.uvs[edge.uvb])
            coords = [ ((uv.u * w), (uv.v * h)) for uv in uvs ]
            draw.line(coords, 255, args.width)

        if res != ssres:
            final = im.resize((res, res), resample=Image.LANCZOS)
        else:
            final = im

        final.save(args.out_file)

    return 0


if __name__ == "__main__":
    sys.exit(main())

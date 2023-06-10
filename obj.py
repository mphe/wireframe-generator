#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
from dataclasses import dataclass
from typing import List


@dataclass
class Vec3:
    x: float
    y: float
    z: float

    def cross(self, other: "Vec3") -> "Vec3":
        return Vec3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def __add__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def normalized(self) -> "Vec3":
        length = self.length()
        return Vec3(self.x / length, self.y / length, self.z / length)

    def length(self) -> float:
        return math.sqrt((self.x ** 2 + self.y ** 2 + self.z ** 2))

    def almostEquals(self, other: "Vec3") -> bool:
        return math.isclose(self.x, other.x, rel_tol=0.1, abs_tol=0.1) \
            and math.isclose(self.y, other.y, rel_tol=0.1, abs_tol=0.1) \
            and math.isclose(self.z, other.z, rel_tol=0.1, abs_tol=0.1)


@dataclass
class UV:
    u: float
    v: float


@dataclass
class Face:
    vertex_idxs: List[int]
    uv_idxs: List[int]

    def normal(self, obj: "Obj") -> Vec3:
        # https://stackoverflow.com/a/22838372/4778400
        normal = Vec3(0.0, 0.0, 0.0)
        for i in range(len(self.vertex_idxs)):
            a: Vec3 = obj.vertices[self.vertex_idxs[i]]
            b: Vec3 = obj.vertices[self.vertex_idxs[(i + 1) % len(self.vertex_idxs)]]
            normal += a.cross(b)

        return normal.normalized()


@dataclass
class Obj:
    vertices: List[Vec3]
    uvs: List[UV]
    faces: List[Face]


def parse_obj(fname: str, flip_uv_y: bool = False) -> Obj:
    vertices: List[Vec3] = []
    uvs: List[UV] = []
    faces: List[Face] = []

    with open(fname, "r") as f:
        for line in f:
            tokens = line.strip().split()

            if not tokens or tokens[0] == "#" or tokens[0] == "":
                continue

            if tokens[0] == "v":
                x, y, z = map(float, tokens[1:4])
                vertices.append(Vec3(x, y, z))

            elif tokens[0] == "vt":
                u, v = map(float, tokens[1:3])
                if flip_uv_y:
                    v = 1.0 - v
                uvs.append(UV(u, v))

            elif tokens[0] == "f":
                # face format: f v/vt/vn v/vt/vn v/vt/vn v/vt/vn
                vertex_idxs: List[int] = []
                uv_idxs: List[int] = []

                for p in tokens[1:]:
                    # tuple format: v/vt/vn
                    indicies = [ int(i) - 1 for i in p.split("/") ]

                    if len(indicies) == 1:
                        vertex_idxs.append(indicies[0])
                        uv_idxs.append(indicies[0])
                    else:
                        vertex_idxs.append(indicies[0])
                        uv_idxs.append(indicies[1])

                faces.append(Face(vertex_idxs, uv_idxs))

    return Obj(vertices, uvs, faces)

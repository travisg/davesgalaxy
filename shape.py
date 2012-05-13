#!/usr/bin/env python

import math
import sys
import unittest


def minus(a, b):
    return (a[0] - b[0], a[1] - b[1])

def plus(a, b):
    return (a[0] + b[0], a[1] + b[1])

def scale(a, s):
    return (s * a[0], s * a[1])

def dot(a, b):
    return (a[0] * b[0]) + (a[1] * b[1])

def magnitude(a):
    return math.sqrt(dot(a, a))

def normal(a):
    return scale(a, 1.0 / magnitude(a))

def distance(a, b):
    return magnitude(minus(a, b))

def point_to_line(p, line):
    a = line[0]
    b = line[1]
    ab = minus(a, b)
    l = abs(dot(ab, ab))
    if l < 0.0001:
        return a
    s = dot(minus(p, b), ab) / l
    if s < 0.0:
        return b
    if s > 1.0:
        return a
    return plus(b, scale(ab, s))
    
class Circle:
    def __init__(self, location, radius):
        self.c = location
        self.r = radius
    def bounding_box(self):
        return ((self.c[0] - self.r, self.c[1] - self.r), 
                (self.c[0] + self.r, self.c[1] + self.r))
    def distance(self, point):
        return distance(point, self.c)
    def inside(self, point):
        return self.distance(point) < self.r
    def nearest_to(self, p):
        return plus(self.c,  scale(normal(minus(p, self.c)), self.r))
        
class Polygon:
    def __init__(self, *points):
        self.points = points
    def bounding_box(self):
        min_x = sys.float_info.max
        min_y = sys.float_info.max
        max_x = -sys.float_info.max
        max_y = -sys.float_info.max
        for vertex in self.points:
            min_x = min(min_x, vertex[0])
            min_y = min(min_y, vertex[1])
            max_x = max(max_x, vertex[0])
            max_y = max(max_y, vertex[1])
        return ((min_x, min_y), (max_x, max_y))
    def distance(self, point):
        c = (0.0, 0.0)
        for vertex in self.points:
            c = plus(vertex, c)
        c = scale(c, 1 / float(len(self.points)))
        return distance(point, c)
    def inside(self, point):
        # http://www.ariel.com.au/a/python-point-int-poly.html
        x = point[0]
        y = point[1]
        n = len(self.points)
        inside = False
        p1x,p1y = self.points[0]
        for i in range(n+1):
            p2x,p2y = self.points[i % n]
            if y > min(p1y,p2y):
                if y <= max(p1y,p2y):
                    if x <= max(p1x,p2x):
                        if p1y != p2y:
                            xinters = ((y - p1y) * (p2x - p1x) / (p2y - p1y)
                                       + p1x)
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x,p1y = p2x,p2y
        return inside
    def nearest_to(self, p):
        min_d = sys.float_info.max
        min_q = None
        last_vertex = self.points[-1]
        for vertex in self.points:
            q = point_to_line(p, (vertex, last_vertex))
            if distance(p, q) < min_d:
                min_d = distance(p, q)
                min_q = q
            last_vertex = vertex
        return min_q


class UnionShape:
    def __init__(self, *shapes):
        self.shapes = shapes
    def bounding_box(self):
        min_x = sys.float_info.max
        min_y = sys.float_info.max
        max_x = -sys.float_info.max
        max_y = -sys.float_info.max
        for shape in self.shapes:
            bb = shape.bounding_box()
            min_x = min(min_x, bb[0][0])
            min_y = min(min_y, bb[0][1])
            max_x = max(max_x, bb[1][0])
            max_y = max(max_y, bb[1][1])
        return ((min_x, min_y), (max_x, max_y))
    def distance(self, point):
        d = sys.float_info.max
        for shape in self.shapes:
            d = min(d, shape.distance(point))
        return d
    def inside(self, point):
        inside = False
        for shape in self.shapes:
            inside = inside or shape.inside(point)
        return inside
    def nearest_to(self, p):
        min_d = sys.float_info.max
        min_q = None
        for shape in self.shapes:
            q = shape.nearest_to(p)
            if distance(p, q) < min_d:
                min_d = distance(p, q)
                min_q = q
        return min_q

class IntersectionShape:
    def __init__(self, *shapes):
        self.shapes = shapes
    def bounding_box(self):
        # this is very loose
        min_x = sys.float_info.max
        min_y = sys.float_info.max
        max_x = -sys.float_info.max
        max_y = -sys.float_info.max
        for shape in self.shapes:
            bb = shape.bounding_box()
            min_x = min(min_x, bb[0][0])
            min_y = min(min_y, bb[0][1])
            max_x = max(max_x, bb[1][0])
            max_y = max(max_y, bb[1][1])
        return ((min_x, min_y), (max_x, max_y))
    def distance(self, point):
        # this too is not accurate
        d = sys.float_info.max
        for shape in self.shapes:
            d = min(d, shape.distance(point))
        return d
    def inside(self, point):
        inside = True
        for shape in self.shapes:
            inside = inside and shape.inside(point)
        return inside
    def nearest_to(self, p):
        sys.stderr.write("IntersectionShape.nearest_to() is not implemented\n")
        assert(false)


def test():
    output = {True: 'inside', False:'outside'}


class TestSequenceFunctions(unittest.TestCase):

    def setUp(self):
        self.circle = Circle((5.0, 2.5), 2.5)
        self.polygon = Polygon((0.0, 0.0), (0.0, 5.0), (6.0, 2.5))
        self.union = UnionShape(self.circle, self.polygon)
        self.intersection = IntersectionShape(self.circle, self.polygon)
        self.a = (1.0, 1.0) # inside poly, outside circle
        self.b = (5.5, 4.0) # inside circle, outside poly
        self.c = (4.0, 2.5) # inside circle, inside poly
        self.d = (10.0, 10.0) # outside circle, outside poly

    def test_circle(self):
        self.assertEqual(False, self.circle.inside(self.a),
                         'a should be ouside the circle')
        self.assertEqual(True, self.circle.inside(self.b),
                         'b should be inside the circle')
        self.assertEqual(True, self.circle.inside(self.c),
                         'c should be inside the circle')
        self.assertEqual(False, self.circle.inside(self.d),
                         'd should be outside the circle')
        self.assertEqual(1.0, self.circle.distance(self.c))
        self.assertEqual(((2.5, 0.0), (7.5, 5.0)),
                         self.circle.bounding_box())
        self.assertEqual((2.5, 2.5), self.circle.nearest_to((0.0, 2.5)))
        self.assertEqual((5.0, 5.0), self.circle.nearest_to((5.0, 10.0)))
    def test_polygon(self):
        self.assertEqual(True, self.polygon.inside(self.a),
                         'a should be inside the polygon')
        self.assertEqual(False, self.polygon.inside(self.b),
                         'b should be outside the polygon')
        self.assertEqual(True, self.polygon.inside(self.c),
                         'c should be inside the polygon')
        self.assertEqual(False, self.polygon.inside(self.d),
                         'd should be outside the polygon')
        self.assertEqual(2.0, self.polygon.distance(self.c))
        self.assertEqual(((0.0, 0.0), (6.0, 5.0)),
                         self.polygon.bounding_box())
        self.assertEqual((0.0, 0.0), self.polygon.nearest_to((0.0, 0.0)))
        self.assertEqual((0.0, 5.0), self.polygon.nearest_to((0.0, 5.0)))
        self.assertEqual((0.0, 2.5), self.polygon.nearest_to((0.1, 2.5)))
        self.assertEqual((0.0, 2.6), self.polygon.nearest_to((-0.1, 2.6)))
        self.assertEqual((6.0, 2.5), self.polygon.nearest_to((6.5, 2.5)))
    def test_union(self):
        self.assertEqual(True, self.union.inside(self.a),
                         'a should be inside the union')
        self.assertEqual(True, self.union.inside(self.b),
                         'b should be inside the union')
        self.assertEqual(True, self.union.inside(self.c),
                         'c should be inside the union')
        self.assertEqual(False, self.union.inside(self.d),
                         'd should be outside the union')
        self.assertEqual(1.0, self.union.distance(self.c))
        self.assertEqual(((0.0, 0.0), (7.5, 5.0)),
                         self.union.bounding_box())
        self.assertEqual((0.0, 2.5), self.union.nearest_to((0.0, 2.5)))
        self.assertEqual((5.0, 5.0), self.union.nearest_to((5.0, 10.0)))
        self.assertEqual((0.0, 0.0), self.union.nearest_to((0.0, 0.0)))
        self.assertEqual((0.0, 5.0), self.union.nearest_to((0.0, 5.0)))
        self.assertEqual((0.0, 2.5), self.union.nearest_to((0.1, 2.5)))
        self.assertEqual((0.0, 2.6), self.union.nearest_to((-0.1, 2.6)))
        self.assertEqual((6.0, 2.5), self.union.nearest_to((6.5, 2.5)))
    def test_intersection(self):
        self.assertEqual(False, self.intersection.inside(self.a),
                         'a should be outside the intersection')
        self.assertEqual(False, self.intersection.inside(self.b),
                         'b should be outside the intersection')
        self.assertEqual(True, self.intersection.inside(self.c),
                         'c should be inside the intersection')
        self.assertEqual(False, self.intersection.inside(self.d),
                         'd should be outside the intersection')
        self.assertEqual(1.0, self.intersection.distance(self.c))
        self.assertEqual(((0.0, 0.0), (7.5, 5.0)),
                         self.intersection.bounding_box())
        # don't test intersection.nearest_to until we fix it.

if __name__ == '__main__':
    unittest.main()

import math
import xml.etree.ElementTree as ET

import utm

IMPORTANT_TAGS = ["highway", "place", "amenity", "shop", "building",
                  "landuse", "natural", "leisure", "office", "waterway",
                  "power"]


class SVGElement:
    def __init__(self, name):
        self.name = name
        self._attributes = dict()
        self.childs = []
        self.coords = []

    def set_attributes(self, attributes: dict):
        self._attributes.update(attributes)

    def get_attributes(self):
        return self._attributes

    def add_child(self, child):
        self.childs.append(child)


class SVGMarker(SVGElement):
    def __init__(self, x, y):
        super().__init__(name="path")
        d = "M{x},{y} a -15 -25 0 0 1 25 0 l -12 25 z".format(**vars())
        self._attributes = {'d': d, "class": "marker"}


class SVGText:
    def __init__(self, text):
        self.text = text

    def to_str(self):
        return self.text


class SVG:
    def __init__(self, width=500, height=400):
        self.root = None
        self.width = width
        self.height = height

    def _create_root(self):
        self.root = SVGElement(name='svg')
        self.root.set_attributes({'class': "svg",
                                  'width': self.width,
                                  'height': self.height})

    def from_xml(self, xml_map):
        """Create SVG tree from XMLMap"""
        self._create_root()
        self.bound_coords = xml_map.get_bound_coords()
        for way in xml_map.ways:
            line_coords = xml_map.get_way_coords(way)
            if line_coords:
                el = SVGElement(name="polyline")
                el.coords = [utm.from_latlon(*coords)[:2] for coords in line_coords]
                el_classes = xml_map.get_way_classes(way)
                el.set_attributes({"class": " ".join(el_classes),
                                   "id": way.attrib["id"]})

                self.root.add_child(el)
 
    def to_str(self, el, scale, x, y):
        coords_on_map = [self.utm_coords_on_map(x, y, *coords, scale) for coords in el.coords] 
        if self.is_visible_element(coords_on_map) or el is self.root:
            attr = ['{}="{}"'.format(k, v) for k, v in el.get_attributes().items()]
            if coords_on_map:
                # reduce unnecessary precision
                points = " ".join(["{:.4f},{:.4f}".format(*coords)
                                   for coords in coords_on_map])
                attr.append('points="{}"'.format(points))
            result = "<{name} {attributes}>".format(name=el.name,
                                                    attributes=" ".join(attr))
            if el.childs:
                for child in el.childs:
                    s = self.to_str(child, scale, x, y)
                    if s is not None:
                        result += s
                result += "</{name}>".format(name=el.name)
            else:
                result = result[:-1] + '/' + result[-1:]
            return result + '\n'

    def get_right_coords(self, lat=0, lon=0):
        min_lat, min_lon = self.bound_coords["min"]
        max_lon, max_lon = self.bound_coords["max"] 
        lat = lat if min_lat < lat < max_lat else min_lat
        lon = lon if min_lon < lon < max_lon else min_lon
        return lat, lon

    def get_content(self, scale, lat, lon):
        x, y, *_ = utm.from_latlon(lat, lon)
        return self.to_str(self.root, scale, x, y)

    def _get_element_stroke_size(self, coords):
        points_num = len(coords)
        perimeter = 0
        for i in range(points_num):
            if i < points_num - 1:
                x1, y1 = coords[i]
                x2, y2 = coords[i+1]
                perimeter += math.sqrt((x2 - x1)**2 + (y1 - y2)**2)
        return (perimeter / self.width) * 100

    def _is_visible_on_map(self, coords) -> bool:
        """Return True if at least one point of element is visible on map
           otherwise return False
        """
        for x, y in coords:
            if (0 < x < self.width)  and (0 < y < self.height):
                return True
        return False

    def is_visible_element(self, coords, visible_percent=3):
        return (self._is_visible_on_map(coords) and
                self._get_element_stroke_size(coords) >= visible_percent)
    
    def utm_coords_on_map(self, x1, y1, x2, y2, scale):
        return (x2 - x1)*scale, self.height - (y2 -y1)*scale


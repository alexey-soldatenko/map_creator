import math
import xml.etree.ElementTree as ET

IMPORTANT_TAGS = ["highway", "place", "amenity", "shop", "building",
                  "landuse", "natural", "leisure", "office", "waterway", "power"]

class SVGElement:
    def __init__(self, name):
        self.name = name
        self._attributes = dict()
        self.childs = []
        self.coords = []

    def to_str(self):
        attr = ['{}="{}"'.format(k, v) for k, v in self._attributes.items()]
        s = "<{name} {attributes}>".format(name=self.name,
                                           attributes=" ".join(attr))
        if self.childs:
            for child in self.childs:
                s += child.to_str()
            s += "</{name}>".format(name=self.name)
        else:
            s = s[:-1] + '/' + s[-1:]
        return s + '\n'

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
    def __init__(self, scale, offset_x=0, offset_y=0, width=500, height=400):
        self.root = None
        self.scale = scale
        self.width = width
        self.height = height
        self.offset = (offset_x, offset_y)

    def _create_root(self):
        self.root = SVGElement(name='svg')
        self.root.set_attributes({'class': "svg", 'width': self.width, 'height': self.height})

    def from_xml(self, xml_map):
        """Create SVG tree from XMLMap"""
        self._create_root()
        bound_coords = xml_map.get_bound_coords()["min"]
        for way in xml_map.ways:
            line_coords = xml_map.get_way_coords(way)
            if line_coords:
                el = SVGElement(name="polyline")
                el.coords = [self.coords_to_2d(*bound_coords, *coords) for coords in line_coords]
                points = " ".join(["{},{}".format(*coords) for coords in el.coords])
                el_classes = xml_map.get_way_classes(way)
                el.set_attributes({"class": " ".join(el_classes),
                               "points": points,
                               "id": way.attrib["id"]})

                if self.is_visible_element(el):
                    self.root.add_child(el)
 
    def to_str(self):
        if self.root:
            return self.root.to_str()

    def is_visible_element(self, element, visible_percent=3):
        points_num = len(element.coords)
        perimeter = 0
        for i in range(points_num):
            if i < points_num - 1:
                x1, y1 = element.coords[i]
                x2, y2 = element.coords[i+1]
                perimeter += math.sqrt((x2 - x1)**2 + (y1 - y2)**2)
        percent = (perimeter / self.width) * 100
        if percent > visible_percent:
            return True
        return False

    def coords_to_2d(self, x1, y1, x2, y2):
        dx = (y2-y1)*40000*math.cos((x1+x2)*math.pi/360)/360
        dy = (x2-x1)*40000/360
        return dx*self.scale + self.offset[0], self.height/2 - dy*self.scale - self.offset[1]


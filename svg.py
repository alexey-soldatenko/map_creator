import math
import xml.etree.ElementTree as ET

IMPORTANT_TAGS = ["highway", "place", "amenity", "shop", "building", "landuse", "natural", "leisure", "office", "waterway", "power"]

class SVGElement:
    def __init__(self, name):
        self.name = name
        self._attributes = dict()
        self.childs = []

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
    def __init__(self, xml_path, scale, width=500, height=400):
        self.xml_path = xml_path
        self.xml_tree = None
        self.root = None
        self.scale = scale
        self.width = width
        self.height = height

    def parse_xml(self):
        return ET.parse(self.xml_path)

    def get_map_coords(self, xml_tree):
        bounds = xml_tree.find('bounds')
        coords = {k:float(v) for k, v in bounds.attrib.items()
                  if k in ['minlat', 'minlon', 'maxlat', 'maxlon']}
        return ((coords['minlat'], coords['minlon']),
                (coords['maxlat'], coords['maxlon']))

    def from_xml(self):
        self.xml_tree = self.parse_xml()
        ways = self.xml_tree.findall('way')
        relations = self.get_relations(self.xml_tree.findall('relation'))
        nodes = {node.attrib['id']:node for node in self.xml_tree.findall('node')}
        x, y = self.get_map_coords(self.xml_tree)[0]
        self.root = SVGElement(name='svg')
        self.root.set_attributes({'class': "svg", 'width': self.width, 'height': self.height})

        text_elements = []
        for way in ways:
            childs = way.getchildren()
            line_coords = []
            el_classes = set()
            el = SVGElement(name="polyline")
            way_name = ""
            for child in childs:
                if child.tag == "nd":
                    node = nodes[child.attrib['ref']]
                    x1, y1 = (float(node.attrib['lat']),
                              float(node.attrib['lon']))
                    line_coords.append(self.coords_to_2d(x, y, x1, y1))
                elif child.tag == 'tag':
                    if child.attrib['k'] == "name":
                        way_name = child.attrib['v']
                    if child.attrib['k'] in IMPORTANT_TAGS:
                        el_classes.add(child.attrib['k'])
                        el_classes.add(child.attrib['v'])
            for key, ids in relations.items():
                if way.attrib['id'] in ids:
                    el_classes.add(key)
                    break
            if line_coords:
                points = " ".join(["{},{}".format(*coords)
                                   for coords in line_coords])
                el.set_attributes({'class': " ".join(el_classes), 'points': points, "data-name": way_name})
                if self.is_visible_element(line_coords):
                    self.root.add_child(el)
                    if way_name:
                        text = SVGElement(name="text")
                        text.set_attributes({'x': line_coords[0][0], 'y': line_coords[0][1], "class": "text"})
                        text.add_child(SVGText(way_name))
                        text_elements.append(text)
        #for text in text_elements:
        #    self.root.add_child(text)

        #self.root.add_child(SVGMarker(200, 200))

    def get_relations(self, xml_relations):
        result = dict()
        for relation in xml_relations:
            members = set()
            tag = ""
            for node in relation.getchildren():
                if node.tag == "member":
                    members.add(node.attrib["ref"])
                elif node.tag == 'tag' and node.attrib['k'] in IMPORTANT_TAGS:
                    tag = node.attrib['k']
            if tag:
                result[tag] = result.get(tag, set()) | members
        return result


    def to_str(self):
        if self.root:
            return self.root.to_str()

    def is_visible_element(self, points, visible_percent=3):
        points_num = len(points)
        perimeter = 0
        for i in range(points_num):
            if i < points_num - 1:
                x1, y1 = points[i]
                x2, y2 = points[i+1]
                perimeter += math.sqrt((x2 - x1)**2 + (y1 - y2)**2)
        percent = (perimeter / self.width) * 100
        if percent > visible_percent:
            return True
        return False

    def coords_to_2d(self, x1, y1, x2, y2):
        dx = (y2-y1)*40000*math.cos((x1+x2)*math.pi/360)/360
        dy = (x2-x1)*40000/360
        return dx*self.scale, self.height/2 - dy*self.scale


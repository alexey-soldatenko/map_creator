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

    def create_root(self):
        self.root = SVGElement(name='svg')
        self.root.set_attributes({'class': "svg", 'width': self.width, 'height': self.height})

    def get_classes_by_element_id(self, element_id):
        el_classes = set()
        for class_names, ids in self.relations.items():
            if element_id in ids:
                for class_name in class_names:
                    el_classes.add(class_name)
        return el_classes

    def get_common_classes(self, tags):
        el_classes = set()
        for tag, value in tags.items():
            if tag in IMPORTANT_TAGS:
                el_classes |= set([tag, value])
        return el_classes

    def get_classes_for_highway(self, tags):
        el_classes = set()
        lanes = int(tags.get("lanes", 0))
        nat_ref = tags.get("nat_ref")
        if lanes >= 2:
            lanes_class = "highway_big" if lanes > 2 else "highway_middle"
            el_classes.add(lanes_class)
        if nat_ref:
            el_classes.add("national_way")
        return el_classes

    def create_way_element(self, way):
        el = SVGElement(name="polyline")
        line_coords = []
        el_classes = set()
        tags = dict()
        way_name = tags.get("name", "")
        for child in way.getchildren():
            if child.tag == "nd":
                node = self.nodes[child.attrib['ref']]
                x1, y1 = (float(node.attrib['lat']),
                          float(node.attrib['lon']))
                line_coords.append(self.coords_to_2d(self.x, self.y, x1, y1))
            elif child.tag == 'tag':
                tags[child.attrib['k']] = child.attrib['v']
        el_classes |= self.get_common_classes(tags)
        el_classes |= self.get_classes_by_element_id(way.attrib['id'])
        el_classes |= self.get_classes_for_highway(tags)
        if line_coords:
            el.coords = line_coords
            points = " ".join(["{},{}".format(*coords)
                               for coords in line_coords])
            el.set_attributes({"class": " ".join(el_classes),
                               "points": points,
                               "data-name": way_name,
                               "id": way.attrib["id"]})
        return el

    def set_data_from_xml(self):
        self.xml_tree = self.parse_xml()
        self.ways = self.xml_tree.findall('way')
        self.relations = self.get_relations(self.xml_tree.findall('relation'))
        self.nodes = {node.attrib['id']: node for node in self.xml_tree.findall('node')}
        self.x, self.y = self.get_map_coords(self.xml_tree)[0] 
                
    def from_xml(self):
        self.create_root()
        self.set_data_from_xml()
        for way in self.ways:
            el = self.create_way_element(way)
            if self.is_visible_element(el):
                self.root.add_child(el)
                
    def get_relations(self, xml_relations):
        result = dict()
        for relation in xml_relations:
            members = set()
            tag = tuple()
            for node in relation.getchildren():
                if node.tag == "member":
                    members.add(node.attrib["ref"])
                elif node.tag == 'tag' and node.attrib['k'] in IMPORTANT_TAGS:
                    tag = tag + (node.attrib['k'], node.attrib['v'])
            if tag:
                result[tag] = result.get(tag, set()) | members
        return result


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
        return dx*self.scale, self.height/2 - dy*self.scale


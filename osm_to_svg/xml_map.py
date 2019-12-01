import xml.etree.ElementTree as ET

IMPORTANT_TAGS = ["highway", "place", "amenity", "shop", "building",
                  "landuse", "natural", "leisure", "office", "waterway",
                  "power"]


class XMLMap:
    def __init__(self, path):
        self.path = path
        self.tree = ET.parse(path)
        self._ways = None
        self._relations = None
        self._nodes = None
        self._bounds = None
        self._cached_tags = dict()

    @property
    def ways(self) -> list:
        if not self._ways:
            self._ways = self.tree.findall('way')
        return self._ways

    @property
    def relations(self) -> list:
        if not self._relations:
            self._relations = self.tree.findall('relation')
        return self._relations

    @property
    def nodes(self) -> dict:
        if not self._nodes:
            self._nodes = {node.attrib['id']: node
                           for node in self.tree.findall('node')}
        return self._nodes

    def get_bound_coords(self) -> dict:
        """Return map bounds coordinats"""
        bounds = self.tree.find('bounds')
        return {"min": (float(bounds.attrib['minlat']),
                        float(bounds.attrib['minlon'])),
                "max": (float(bounds.attrib['maxlat']),
                        float(bounds.attrib['maxlon']))}

    def tags_with_element_ids(self) -> dict:
        if not self._cached_tags:
            for relation in self.relations:
                tags = tuple()
                for node in relation.findall('tag'):
                    if node.attrib['k'] in IMPORTANT_TAGS:
                        tags = tags + (node.attrib['k'], node.attrib['v'])
                if tags:
                    members = {member.attrib["ref"]
                               for member in relation.findall("member")}
                    self._cached_tags[tags] = (
                        self._cached_tags.get(tags, set()) | members)
        return self._cached_tags

    def get_node_coords(self, node) -> tuple:
        return float(node.attrib['lat']), float(node.attrib['lon'])

    def get_way_coords(self, way) -> list:
        """Return list of tuples with coordinats of way points """
        coords = []
        for nd in way.findall('nd'):
            x1, y1 = self.get_node_coords(self.nodes[nd.attrib['ref']])
            coords.append((x1, y1))
        return coords

    def get_way_classes(self, way) -> set:
        """Return set of name classes for *way*"""
        el_classes = set()
        tags = {tag.attrib['k']: tag.attrib['v']
                for tag in way.findall("tag")}
        el_classes |= self._get_common_classes(tags)
        el_classes |= self._get_classes_by_element_id(way.attrib['id'])
        el_classes |= self._get_classes_for_highway(tags)
        return el_classes

    def _get_classes_by_element_id(self, element_id) -> set:
        """Return set of classes of relation to which *id* is related"""
        el_classes = set()
        for class_names, ids in self.tags_with_element_ids().items():
            if element_id in ids:
                for class_name in class_names:
                    el_classes.add(class_name)
        return el_classes

    def _get_common_classes(self, tags) -> set:
        """Return set of classes by element *tags*"""
        el_classes = set()
        for tag, value in tags.items():
            if tag in IMPORTANT_TAGS:
                el_classes |= set([tag, value])
        return el_classes

    def _get_classes_for_highway(self, tags) -> set:
        """Return set of classes intended only for highway"""
        el_classes = set()
        lanes = int(tags.get("lanes", 0))
        nat_ref = tags.get("nat_ref")
        if lanes >= 2:
            lanes_class = "highway_big" if lanes > 2 else "highway_middle"
            el_classes.add(lanes_class)
        if nat_ref:
            el_classes.add("national_way")
        return el_classes


import json

from flask import Flask, render_template, request
import utm

from osm_to_svg.svg import SVG
from osm_to_svg.xml_map import XMLMap

SCALE_INIT = 1/20

app = Flask(__name__)

xml_map = XMLMap("../map_big.osm")
svg = SVG(width=700, height=500)
svg.from_xml(xml_map)


def get_coords_for_scale(x, y, offset_x, offset_y, current_scale, needed_scale, width, height):
    if width/2 > offset_x:
        delta_x = -((width/2 - offset_x)/current_scale) 
    else:
        delta_x = (width/2 - (width - offset_x))/current_scale
    middle_x = x + delta_x + (width/current_scale)/2  # x center for current scale
    middle_y = y + (height - offset_y)/current_scale  # y center for current scale
    need_width = width/needed_scale
    need_height = height/needed_scale
    # left top angle
    x = middle_x - need_width/2
    y = middle_y - need_height/2
    return x, y


@app.route('/')
def get_map():
    lat, lon = svg.get_right_coords()
    return render_template('base.html',
                           svg_content=svg.get_content(SCALE_INIT, lat, lon),
                           latitude=lat,
                           longitude=lon)


@app.route('/zoom', methods=["POST"])
def zoom():
    print(request.json)
    zoom = request.json.get("zoom", 1)
    lat = request.json.get("x")
    lon = request.json.get("y")
    offset_x = request.json.get("offset_x", 0)
    offset_y = request.json.get("offset_y", 0)
    current_scale = SCALE_INIT*zoom 
    zoom += 1 if request.json.get("is_increased_map", True) else -1 
    if 1 <= zoom <= 10:
        needed_scale = SCALE_INIT*zoom
        if not lat and not lon:
            lat, lon = svg.get_right_coords()
        x, y, zone_number, zone_letter = utm.from_latlon(lat, lon)
        x, y = get_coords_for_scale(x, y, offset_x, offset_y, current_scale, needed_scale, svg.width, svg.height)
        lat, lon = utm.to_latlon(x, y, zone_number, zone_letter)
        content = svg.get_content(SCALE_INIT*zoom, lat, lon)
        result = {'x': lat, 'y':lon, 'zoom': zoom, 'svg_content': content, 'status': 'ok', 'message': ''}
    else:
        result = {'status': "error", 'message': 'Limit of zoom'}
    return json.dumps(result)

if __name__ == '__main__':
    app.run()

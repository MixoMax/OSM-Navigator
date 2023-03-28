import requests
import math
import pygame as pg
import time
import xml.etree.ElementTree as ET
from tqdm import tqdm
import keyboard



class Node():
    def __init__(self, id, lat, lon):
        self.id = id
        
        self.lat = lat
        self.lon = lon
        
        self.neighbors = [()] # [(id, distance), ...]
    
    def add_neighbor(self, neighbor):
        self.neighbors.append(neighbor)
    
    def get_neighbors(self):
        return self.neighbors
        

class Street():
    def __init__(self, id, start, end):
        self.id = id
        
        self.start = start
        self.end = end
        
        start.add_neighbor((end.id, self.length()))
        end.add_neighbor((start.id, self.length()))
        
    def length(self):
        return math.sqrt((self.start.lat - self.end.lat)**2 + (self.start.lon - self.end.lon)**2)
    
    def angle(self):
        return math.atan2(self.end.lat - self.start.lat, self.end.lon - self.start.lon)


class OSM():
    def __init__(self):
        self.api = "https://api.openstreetmap.org/api/0.6/map?bbox="
    
    def get_map(self, pos1, pos2):
        min_lat = min(pos1[0], pos2[0])
        max_lat = max(pos1[0], pos2[0])
        
        min_lon = min(pos1[1], pos2[1])
        max_lon = max(pos1[1], pos2[1])
        
        bbox = f"{min_lat},{min_lon},{max_lat},{max_lon}"
        
        r = requests.get(self.api + bbox)
        return r.text
    
    def get_map_by_GPS(self, pos):
        bbox = f"{pos.lon - 0.01},{pos.lat - 0.01},{pos.lon + 0.01},{pos.lat + 0.01}"
        
        r = requests.get(self.api + bbox)
        return r.text
    
    def get_overview_map(self):
        r = requests.get(self.api + "-180,-90,180,90")
        return r.text


class GPS():
    def __init__(self, lat, lon, accuracy = 0):
        self.lat = lat
        self.lon = lon
        self.accuracy = accuracy
    
    def get_pos(self):
        return (self.lat, self.lon)
    
    def __iter__(self):
        return iter((self.lat, self.lon))


def pg_init():
    pg.init()
    pg.display.set_caption("Map")
    screen = pg.display.set_mode((800, 600))
    return screen

def draw_map(screen, streets, nodes, zoom, pos):
    
    print(zoom)
    
    # Define the boundaries of the map
    # You can adjust these values to fit your map
    
    map_width = screen.get_width()
    map_height = screen.get_height()
    
    margin = 20 
    
    lats = []
    lons = []
    
    
    for key, street in streets.items():
        if type(street) == Street:
            lats.append(street.start.lat)
            lats.append(street.end.lat)
            lons.append(street.start.lon)
            lons.append(street.end.lon)
        else:
            print(key, street)
    
    for key, node in nodes.items():
        if type(node) == Node:
            lats.append(node.lat)
            lons.append(node.lon)
        else:
            print(key, node)

    min_lat = min(lats)
    max_lat = max(lats)
    min_lon = min(lons)
    max_lon = max(lons)

    # Calculate the multipliers for converting latitudes and longitudes to pixels
    lat_multiplier = (map_height - 2 * margin) / ((max_lat - min_lat) * zoom)
    lon_multiplier = (map_width - 2 * margin) / ((max_lon - min_lon) * zoom)

    # Transform the latitudes and longitudes to screen coordinates
    for key, street in streets.items():
        if type(street) != Street:
            print(street)
            continue
        start_x = int((street.start.lon - min_lon) * lon_multiplier * zoom + margin - pos.lon)
        start_y = int((max_lat - street.start.lat) * lat_multiplier * zoom + margin - pos.lat)
        end_x = int((street.end.lon - min_lon) * lon_multiplier * zoom + margin - pos.lon)
        end_y = int((max_lat - street.end.lat) * lat_multiplier * zoom + margin - pos.lat)
        pg.draw.line(screen, (255, 255, 255), (start_x, start_y), (end_x, end_y), 2)

    for key, node in nodes.items():
        if type(node) != Node:
            print(node)
            continue
        x = int((node.lon - min_lon) * lon_multiplier * zoom + margin - pos.lon)
        y = int((max_lat - node.lat) * lat_multiplier * zoom + margin - pos.lat)
        pg.draw.circle(screen, (255, 0, 0), (x, y), 3)



def parse_map(xml_str):
    
    print(xml_str)
    
    root = ET.fromstring(xml_str)
    
    nodes = {} # {id: Node}
    streets = {} # {id: Street}
    
    for node_elem in root.iter("node"):
        node_id = node_elem.attrib["id"]
        node_lat = float(node_elem.attrib["lat"])
        node_lon = float(node_elem.attrib["lon"])
        nodes[node_id] = Node(node_id, node_lat, node_lon)
        
    for way_elem in root.iter("way"):
        if any(tag.attrib["k"] == "highway" for tag in way_elem.iter("tag")):
            way_id = way_elem.attrib["id"]
            way_nodes = way_elem.findall("./nd")
            if len(way_nodes) > 1:
                start_node = nodes[way_nodes[0].attrib["ref"]]
                end_node = nodes[way_nodes[-1].attrib["ref"]]
                streets[way_id] = Street(way_id, start_node, end_node)
                for i in range(len(way_nodes) - 1):
                    curr_node = nodes[way_nodes[i].attrib["ref"]]
                    next_node = nodes[way_nodes[i+1].attrib["ref"]]
                    dist = Street(None, curr_node, next_node).length()
                    curr_node.add_neighbor((next_node.id, dist))
                    next_node.add_neighbor((curr_node.id, dist))
    
    return streets, nodes


def main():
    osm = OSM()
    
    pos = GPS(52.520008, 13.404954)
    
    
    map_xml = osm.get_map_by_GPS(pos)
    
    streets, nodes = parse_map(map_xml)
    
    
    
    screen = pg_init()
    
    
    
    # Main loop
    
    zoom_level = 1 # percent
    zoom_speed = 1
    
    screen.fill((0, 0, 0))
    draw_map(screen, streets, nodes, zoom_level, pos)
    pg.display.flip()
    
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                return
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    pg.quit()
                    return
        prev_zoom = zoom_level
        time.sleep(1/60)
        
        if keyboard.is_pressed("+"):
            zoom_level += 0.1 * zoom_speed
        if keyboard.is_pressed("-"):
            zoom_level -= 0.1 * zoom_speed
        if keyboard.is_pressed("up"):
            zoom_speed += 0.1
        if keyboard.is_pressed("down"):
            zoom_speed -= 0.1
            
        zoom_level = round(zoom_level, 2)
        
        print("zoom level:", zoom_level, "zoom speed:", zoom_speed, end="\r")
        
        if zoom_level != prev_zoom:
            screen.fill((0, 0, 0))
            draw_map(screen, streets, nodes, zoom_level, pos)
            pg.display.flip()
    

if __name__ == "__main__":
    main()
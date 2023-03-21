import requests
import math
import time


# Construct for storing the data
class Street():
    def __init__(self, name, type, id, start, end, crossings) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.start = start # (lat, lon)
        self.end = end # (lat, lon)
        self.length = math.sqrt((self.end[0] - self.start[0])**2 + (self.end[1] - self.start[1])**2)
        self.angle = math.degrees(math.atan2(self.end[1] - self.start[1], self.end[0] - self.start[0]))
        self.crossings = crossings # array of neighbouring streets ids
    
    def __str__(self) -> str:
        return f"Street: {self.name} ({self.type})"
    
    def __repr__(self) -> str:
        return f"Street: {self.name} ({self.type})"
    
    def __eq__(self, o: object) -> bool:
        if isinstance(o, Street):
            return self.id == o.id
        return False
    
    def __len__(self) -> int:
        return self.length

start = (53.3498, 10.0022)
end = (53.57280242718769, 9.993785804663537)

# Define bounding box
bbox = (min(start[1], end[1]), min(start[0], end[0]), max(start[1], end[1]), max(start[0], end[0]))

# Define Overpass query to get all streets within bounding box
overpass_url = "http://overpass-api.de/api/interpreter"
overpass_query = f"""
    [out:json];
    way["highway"]({bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]});
    out;
    """

# Send Overpass API request
response = requests.get(overpass_url, params={"data": overpass_query})

# Parse response and create Street objects
streets = []
for way in response.json()["elements"]:
    # Check if the way is a street
    if "highway" in way["tags"]:
        # Get street name and type
        name = way["tags"].get("name", "")
        street_type = way["tags"].get("highway", "")
        # Get node coordinates
        nodes_query = f"""
            [out:json];
            node({way["nodes"][0]});
            out;
            """
        nodes_response = requests.get(overpass_url, params={"data": nodes_query})
        start_coords = (nodes_response.json()["elements"][0]["lat"], nodes_response.json()["elements"][0]["lon"])
        nodes_query = f"""
            [out:json];
            node({way["nodes"][-1]});
            out;
            """
        nodes_response = requests.get(overpass_url, params={"data": nodes_query})
        end_coords = (nodes_response.json()["elements"][0]["lat"], nodes_response.json()["elements"][0]["lon"])
        
        # Create Street object
        street = Street(name, street_type, way["id"], start_coords, end_coords, [])
        streets.append(street)

for street in streets:
    print(street)
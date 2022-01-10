class CityPair:
    
    def __init__(self, origin, destination, distance=None, index=None):
        super().__init__()
        self.index = index
        self.origin = origin
        self.destination = destination
        if distance != None:
            self.distance = float(distance)
        else:
            self.distance = -1
    
    def __eq__(self, other):
        if other.index == None: # to allow both loading (self.iata_code == other) and comparison on constraints (self.iata_code == other.iata_code) 
            return self.origin.iata_code == other.origin and self.destination.iata_code == other.destination
        return self.index == other.index

    def __repr__(self):
        if self.index == None:
            return ("{{Origin: {origin}, Destination: {destination}, Distance: {distance}}}").format(**vars(self))
        return ("{{Origin: {origin.iata_code}, Destination: {destination.iata_code}, Distance: {distance}}}").format(**vars(self))
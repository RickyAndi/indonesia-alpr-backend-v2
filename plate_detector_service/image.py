
class Image:

    def __init__ (self, image):
        self.image = image
        self.image_with_bounding_boxes = None
        self.plate_coordinates = []
    
    def addPlateCoordinate(self, plate_coordinate):
        self.plate_coordinates.append(plate_coordinate)
    
    def getImage(self):
        return self.image
    
    def getPlateCoordinates(self):
        return self.plate_coordinates
    
    def setImageWithBoundingBoxes(self, image):
        self.image_with_bounding_boxes = image
    
    def getImageWithBoundingBoxes(self):
        return self.image_with_bounding_boxes
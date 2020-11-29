
class PlateCoordinate:

    def __init__(self, min_x, max_x, min_y, max_y):
        self.min_x = min_x
        self.max_x = max_x

        self.min_y = min_y
        self.max_y = max_y

    def getMinX(self):
        return self.min_x
    
    def getWidth(self):
        return self.max_x
    
    def getMinY(self):
        return self.min_y
    
    def getHeight(self):
        return self.max_y
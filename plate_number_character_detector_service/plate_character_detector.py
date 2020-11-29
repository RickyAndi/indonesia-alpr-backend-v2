import cv2
import numpy as np

from possible_char import PossibleChar

class PlateCharacterDetector:
    def __init__(self, knn_k=1):
        self.i = 0
        self.knn = cv2.ml.KNearest_create()
        self.knn.setDefaultK(knn_k)

        self.MIN_CHARACTER_RATIO = 0.25 
        self.MAX_CHARACTER_RATIO = 1

        self.WIDTH_OF_CHARACTER_IMAGE = 20
        self.HEIGHT_OF_CHARACTER_IMAGE = 30

    def trainKnn(self, train_data, labels):
        self.knn.train(train_data, cv2.ml.ROW_SAMPLE, labels)
    
    def predictWithKnn(self, image):
        _, npaResults, _, _ = self.knn.findNearest(image, k=1)
        strCurrentChar = str(chr(int(npaResults[0][0])))
        return strCurrentChar

    def grayScalePlate(self, image):
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def binarizePlate(self, image):
        _, binarized = cv2.threshold(image, 120, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        self.i = self.i + 1
        return binarized

    def getContoursOfImage(self, image):
        contours, _  = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return contours

    def sortContours(self, contours):
        i = 0
        boundingBoxes = [cv2.boundingRect(c) for c in contours]
        (cnts, boundingBoxes) = zip(*sorted(zip(contours, boundingBoxes), key=lambda b: b[1][i], reverse=True))
        return cnts

    def filterOnlyPossibleCharacter(self, possibleCharacters):
        return filter(lambda possibleCharacter : possibleCharacter.fltAspectRatio > self.MIN_CHARACTER_RATIO and possibleCharacter.fltAspectRatio < self.MAX_CHARACTER_RATIO
        , possibleCharacters)

    def detectCharacterInPlate(self, image):
        grayScaled = self.grayScalePlate(image)
        binarized = self.binarizePlate(grayScaled)
        contours = self.getContoursOfImage(binarized)
        sorted_contours = self.sortContours(contours)
        
        possible_characters = []
        for contour in sorted_contours:
            possible_characters.append(PossibleChar(contour))

        filteredPossibleCharacter = self.filterOnlyPossibleCharacter(possible_characters)
       
        plate_number = ""
        for possibleCharacter in list(filteredPossibleCharacter):
            character_image = binarized[possibleCharacter.getMinY():possibleCharacter.getMaxY(), possibleCharacter.getMinX():possibleCharacter.getMaxX()]
            resized_character_image = cv2.resize(character_image, (self.WIDTH_OF_CHARACTER_IMAGE, self.HEIGHT_OF_CHARACTER_IMAGE))
            resized_character_image = resized_character_image.reshape((1, self.WIDTH_OF_CHARACTER_IMAGE * self.HEIGHT_OF_CHARACTER_IMAGE))
            detected_character = self.predictWithKnn(np.float32(resized_character_image))
            plate_number = plate_number + detected_character

        return plate_number

        

        

        

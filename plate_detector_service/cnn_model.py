import cv2
import numpy as np

from plate_coordinate import PlateCoordinate

class CNNModel:
    def __init__ (self, cfg_file, weight_file):
        self.net = cv2.dnn.readNetFromDarknet(cfg_file, weight_file)
    
    def predict_plate_number(self, imageClass):
        
        image = imageClass.getImage()
        (H, W) = image.shape[:2]

        blob = cv2.dnn.blobFromImage(
            image, 
            1 / 255.0, 
            (416, 416),
            (0,0,0),
            swapRB=False, 
            crop=False
        )

        self.net.setInput(blob)
        
        ln = self.net.getLayerNames()
        ln = [ln[i[0] - 1] for i in self.net.getUnconnectedOutLayers()]

        layerOutputs = self.net.forward(ln)

        boxes = []
        confidences = []
        classIDs = []

        for output in layerOutputs:
        # loop over each of the detections
            for detection in output:
                scores = detection[5:]
                classID = np.argmax(scores)
                confidence = scores[classID]
                
                box = detection[0:4] * np.array([W, H, W, H])
                (centerX, centerY, width, height) = box.astype("int")
            
                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))

                boxes.append([x, y, int(width), int(height)])
                confidences.append(float(confidence))
                classIDs.append(classID)

        idxs = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.5)

        if len(idxs) > 0:
        # loop over the indexes we are keeping
            for i in idxs.flatten():
                x = boxes[i][0]
                y = boxes[i][1]
                w = boxes[i][2]
                h = boxes[i][3]

                imageClass.addPlateCoordinate(PlateCoordinate(x, w, y, h))

        for plate_coordinate in imageClass.getPlateCoordinates():
            cv2.rectangle(image, (plate_coordinate.getMinX(), plate_coordinate.getMinY(), plate_coordinate.getWidth(), plate_coordinate.getHeight()), (0, 255, 0), 2)
        

        imageClass.setImageWithBoundingBoxes(image)

        return imageClass
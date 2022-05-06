#importing libraries
from keras.preprocessing.image import img_to_array
from keras.models import load_model
import cv2
from keras.preprocessing import image
from reduce import output_list
import numpy as np
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

def build(file):
    print("[Info] loading pre-trained network...")
    model = load_model("Alexnet_last.hdf5")
    imagepath = file

    print("[Info] loading image...")
    img = cv2.imread(imagepath)
    img = cv2.resize(img, (227, 227), cv2.INTER_AREA)
    img = image.img_to_array(img)
    img = np.expand_dims(img, axis=0)
    img = img / 255

    print("[Info] predicting output")
    lst=[]
    prediction = model.predict(img)
    prediction_flatten = prediction.flatten()
    max_val_index = np.argmax(prediction_flatten)
    result = output_list[max_val_index]
    print(result)
    preds = np.sort(prediction_flatten)
    list1 = preds[:-7:-1]
    for j in range(len(list1)):
        for i in range(len(prediction_flatten)):
            if list1[j] == prediction_flatten[i]:
                lst.append("possible result {}: {}".format(j + 1, output_list[i]))
                print("possible result {}: {}".format(j + 1, output_list[i]))

    return result
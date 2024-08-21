import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt

class PeakPredictor:
    def __init__(self, model_path, peaks):
        self.model = tf.keras.models.load_model(model_path)
        self.peaks = peaks

    def predict_peaks(self):
        predictions = []
        for peak in self.peaks:
            pred = self.model.predict(peak.reshape(1, -1))
            predictions.append(pred[0][0])
        return predictions

    def ppg_prediction(self):
        predictions = self.predict_peaks()
        return predictions  # 예측값 반환


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

    def plot_peaks(self):
        predictions = self.predict_peaks()
        plt.figure(figsize=(12, 6))
        for i, peak in enumerate(self.peaks):
            pred = predictions[i]
            color = (1 - pred, 0, pred)  # 0에 가까우면 파란색, 1에 가까우면 빨간색
            plt.plot(range(len(peak)), peak, color=color, alpha=0.5)
        plt.title('Peaks with Prediction Colors')
        plt.xlabel('Sample Index')
        plt.ylabel('Signal Value')
        plt.show()
        return predictions  # 예측값 반환


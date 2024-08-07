from keras.models import Sequential
from keras.layers import Input, Dense, Conv1D, Dropout, MaxPool1D, Flatten
import tensorflow as tf
import matplotlib.pyplot as plt
import numpy as np
from keras.callbacks import ModelCheckpoint
import keras

EPOCH=3

class model:
    def __init__(self, train, test, y_train, y_test):
        self.train=train
        self.test=test
        self.y_train=y_train
        self.y_test=y_test


    def build_model(self):

        input_shape = (self.train.shape[1], 1)
        model = Sequential()
        model.add(keras.layers.Input(shape=input_shape))
        model.add(Conv1D(filters=32, kernel_size=3, activation='relu', kernel_initializer='glorot_uniform'))
        model.add(Conv1D(filters=32, kernel_size=3, activation='relu', kernel_initializer='glorot_uniform'))
        model.add(keras.layers.MaxPooling1D(pool_size=2))
        model.add(Conv1D(filters=32, kernel_size=3, activation='relu', kernel_initializer='glorot_uniform'))
        model.add(Conv1D(filters=32, kernel_size=3, activation='relu', kernel_initializer='glorot_uniform'))
        model.add(keras.layers.MaxPooling1D(pool_size=2))
        model.add(Conv1D(filters=64, kernel_size=3, activation='relu', kernel_initializer='glorot_uniform'))
        # model.add(Conv1D(filters=64, kernel_size=3, activation='relu', kernel_initializer='glorot_uniform'))
        # model.add(keras.layers.MaxPooling1D(pool_size=2))
        # model.add(Conv1D(filters=64, kernel_size=3, activation='relu', kernel_initializer='glorot_uniform'))
        # model.add(Conv1D(filters=64, kernel_size=3, activation='relu', kernel_initializer='glorot_uniform'))
        # model.add(keras.layers.MaxPooling1D(pool_size=2))
        model.add(tf.keras.layers.Flatten())
        model.add(Dense(8, activation='relu', kernel_initializer='glorot_uniform'))
        model.add(tf.keras.layers.Dropout(0.2))
        model.add(Dense(4, activation='relu', kernel_initializer='glorot_uniform'))
        model.add(tf.keras.layers.Dropout(0.2))
        model.add(Dense(1, activation='sigmoid', kernel_initializer='glorot_uniform'))
        model.add(tf.keras.layers.Dropout(0.2))

        model.summary()

        model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
        checkpoint_callback = ModelCheckpoint("best_model.h5", monitor='val_loss', save_best_only=True, mode='min',
                                              verbose=1)
        history = model.fit(self.train, self.y_train, batch_size=8, epochs=EPOCH, validation_data=(self.test, self.y_test))
        predictions = model.predict(self.test)
        score = model.evaluate(self.test, self.y_test, verbose=1)
        pred_np = np.array(predictions)
        print("\nloss= ", score[0], "\n정답률: ", score[1])
        # print("예측")
        # print(np.round(predictions))
        # now=datetime.now()
        # model_name = f'trained_per_peak_{int(score[1] * 100)}.h5'
        # model.save(model_name)

        return history, predictions, score


class plot:
    def __init__(self, history, predictions, score):
        self.history=history
        self.predictions=predictions
        self.score=score

    def loss_accuracy_plot(self):
        pred_np=np.array(self.predictions)
        pred_np_round = np.round(pred_np)
        plt.figure(figsize=(10, 10))

        plt.subplot(2, 2, 1)
        plt.plot(self.history.history['loss'], label='Loss')
        plt.plot(self.history.history['val_loss'], label='Validation Loss')
        plt.legend()
        plt.title('Train - Loss Function')
        plt.ylim(0, 1)

        plt.subplot(2, 2, 2)
        plt.plot(self.history.history['accuracy'], label='Accuracy')
        plt.plot(self.history.history['val_accuracy'], label='Validation Accuracy')
        plt.legend()
        plt.title('Train - Accuracy')
        plt.ylim(0, 1)

        plt.show()

        from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
        cm = confusion_matrix(self.y_test, pred_np_round)
        disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=None)
        disp.plot()
        plt.show()

        # 플랏하는 클래스
        # 다양한 케이스의 테스트데이터를 얻어보자


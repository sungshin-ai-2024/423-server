import json
import os
import joblib
import pickle
import numpy as np
import pandas as pd
import tensorflow as tf
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from django.core.cache import cache
import logging

from .twelveSecFilter import preprocessing, GMM_model_twelve_sec
from .twelveSecPlot import PeakPredictor

logger = logging.getLogger('logger')


class PpgModelPredictor:
    def __init__(self, model_path, gmm_n_path, gmm_p_path, list_pickle_path, chunk_size, overlap):
        self.model_path = model_path
        self.gmm_n_path = gmm_n_path
        self.gmm_p_path = gmm_p_path
        self.list_pickle_path = list_pickle_path
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.model = self.load_model()
        self.gmm_n, self.gmm_p, self.lab0_f, self.lab1_f, self.m_f, self.n_f = self.load_gmm_and_list()

    def load_model(self):
        logger.info("Loading TensorFlow model...")
        model = tf.keras.models.load_model(self.model_path)
        logger.info("TensorFlow model loaded successfully")
        return model

    def load_gmm_and_list(self):
        try:
            gmm_n_from_joblib = joblib.load(self.gmm_n_path)
            logger.debug("gmm_n loaded successfully")

            gmm_p_from_joblib = joblib.load(self.gmm_p_path)
            logger.debug("gmm_p loaded successfully")

            with open(self.list_pickle_path, "rb") as fi:
                test = pickle.load(fi)
            logger.debug("list.pickle loaded successfully")

            lab0_f = test[0]
            lab1_f = test[1]
            m_f = test[2]
            n_f = test[3]

            return gmm_n_from_joblib, gmm_p_from_joblib, lab0_f, lab1_f, m_f, n_f
        except Exception as e:
            logger.error(f"Error loading files: {e}")
            raise e

    def ppg_process_and_predict(self, ppg_data):
        try:
            ppg_data_list = [float(item) for item in ppg_data]
            if not ppg_data_list:
                logger.error('ppg_data_list is empty or invalid')
                return None, None, 'ppg_data_list is empty or invalid'

            test_data_list = [[1] + ppg_data_list]

            test_filtered = preprocessing(data=test_data_list, chunk_size=self.chunk_size, overlap=self.overlap)
            logger.debug(f"DEBUG: test_filtered = {test_filtered}")
            twelve_sec_filtered, twelve_sec_x, twelve_sec_y = test_filtered.dividing_and_extracting()

            if twelve_sec_filtered is None or twelve_sec_x is None or twelve_sec_y is None:
                logger.error('Testing preprocessing failed, resulting in None data.')
                return None, None, 'Testing preprocessing failed, resulting in None data.'

            logger.debug(f"Shape of twelve_sec_filtered: {np.array(twelve_sec_filtered).shape}")
            logger.debug(f"Shape of twelve_sec_x: {np.array(twelve_sec_x).shape}")
            logger.debug(f"Shape of twelve_sec_y: {np.array(twelve_sec_y).shape}")

            model_for_twelve_sec = GMM_model_twelve_sec(twelve_sec_filtered, self.gmm_p, self.gmm_n,
                                                        self.lab0_f, self.lab1_f, self.m_f, self.n_f)
            x_test_twelve_sec, y_test_twelve_sec = model_for_twelve_sec.GMM_model()
            logger.debug(f"Shape of x_test_twelve_sec after GMM_model: {np.array(x_test_twelve_sec).shape}")
            logger.debug(f"Shape of y_test_twelve_sec after GMM_model: {np.array(y_test_twelve_sec).shape}")

            if x_test_twelve_sec is None or y_test_twelve_sec is None:
                logger.error('Modeling failed, resulting in None data.')
                return None, None, 'Modeling failed, resulting in None data.'

            logger.debug(f"Shape of x_test_twelve_sec: {np.array(x_test_twelve_sec).shape}")
            logger.debug(f"Shape of y_test_twelve_sec: {np.array(y_test_twelve_sec).shape}")

            predictor = PeakPredictor(self.model_path, x_test_twelve_sec)
            y_test_twelve_sec = predictor.plot_peaks()

            if not y_test_twelve_sec:
                logger.error('Prediction resulted in empty data.')
                return x_test_twelve_sec, None, 'Prediction resulted in empty data.'

            return x_test_twelve_sec, y_test_twelve_sec, None
        except Exception as e:
            logger.error(f"Exception: {str(e)}")
            return None, None, str(e)


class AccDataProcessor:
    def __init__(self):
        pass

    def svm_process(self, data):
        try:
            df = pd.DataFrame(data, columns=['x', 'y', 'z'])
            df['SVMacc'] = (df['x'] ** 2 + df['y'] ** 2 + df['z'] ** 2) ** 0.5
            df['SVMacc'] = df['SVMacc'].round(6)
            df.drop(['x', 'y', 'z'], axis=1, inplace=True)
            df = df.transpose()
            return df
        except Exception as e:
            logger.error(f"Failed to read or process data: {e}")
            return None

    def overlap_df(self, data, window_size=300, step_size=300):
        if data is not None:
            data = data.values.reshape(-1, 1)
            data = pd.DataFrame(data, columns=['value'])

            slicing_window = []
            for start in range(0, len(data) - window_size + 1, step_size):
                end = start + window_size
                window = data.iloc[start:end].values.flatten()
                slicing_window.append(window)
            new_df = pd.DataFrame(slicing_window)
            return new_df
        else:
            logger.error("Data is not available")
            return None


class SendGroupConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'send_group'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.info(f"WebSocket connected: {self.channel_name}")

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info(f"WebSocket disconnected: {self.channel_name}")

    async def receive(self, text_data=None, bytes_data=None):
        logger.info(f"Received data: {text_data}")
        data = json.loads(text_data)
        uuid = data.get('uuid')
        ppg_data_str = data.get('ppg')
        acc_data_str = data.get('acc')

        logger.debug(f"Received ppg_data (raw string): {ppg_data_str}")

        try:
            ppg_data = json.loads(ppg_data_str)
            acc_data = json.loads(acc_data_str)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding ppg_data: {e}")
            logger.error(f"Error decoding acc_data: {e}")
            await self.send(text_data=json.dumps({'error': 'Invalid ppg_data format'}))
            return

        logger.debug(f"Decoded ppg_data: {ppg_data}")

        if not isinstance(ppg_data, list):
            logger.error('ppg_data is not a list')
            await self.send(text_data=json.dumps({'error': 'ppg_data is not a list'}))
            return

        if not isinstance(acc_data, list):
            logger.error('acc_data is not a list')
            await self.send(text_data=json.dumps({'error': 'acc_data is not a list'}))
            return

        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, "best_model.h5")
        gmm_n_path = os.path.join(base_dir, 'gmm_n_v3.pkl')
        gmm_p_path = os.path.join(base_dir, 'gmm_p_v3.pkl')
        list_pickle_path = os.path.join(base_dir, 'list_v3.pickle')
        chunk_size = 300
        overlap = 0

        # acc
        processor = AccDataProcessor()
        processed_data = processor.svm_process(acc_data)

        if processed_data is None:
            logger.error('Processing data failed.')
            await self.send(text_data=json.dumps({'error': 'Processing data failed'}))
            return

        overlapped_data = processor.overlap_df(processed_data)

        if overlapped_data is None:
            logger.error('Overlapping data failed.')
            await self.send(text_data=json.dumps({'error': 'Overlapping data failed'}))
            return

        overlapped_data = overlapped_data.values
        overlapped_data = overlapped_data.reshape(overlapped_data.shape[0], overlapped_data.shape[1], 1)

        model_path_acc = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'train_v2.h5')
        model_acc = tf.keras.models.load_model(model_path_acc)
        predictions_acc = model_acc.predict(overlapped_data)
        predicted_classes_acc = np.argmax(predictions_acc, axis=1)

        predictor = PpgModelPredictor(model_path, gmm_n_path, gmm_p_path, list_pickle_path, chunk_size, overlap)
        x_test_twelve_sec, predictions, error = predictor.ppg_process_and_predict(ppg_data)

        if error:
            logger.error(f"Prediction error: {error}")
            await self.send(text_data=json.dumps({'error': error}))
        else:
            y_test_twelve_sec = [float(pred) for pred in predictions]

            # 캐시에 저장
            cache.set(f'ppg_data_storage_{uuid}', x_test_twelve_sec.tolist(), timeout=3600)
            cache.set(f'prediction_results_{uuid}', y_test_twelve_sec, timeout=3600)
            logger.debug(f"Stored normalized ppg_data in cache: {cache.get(f'ppg_data_storage_{uuid}')}")

            # acc
            cache.set(f'acc_data_storage_{uuid}', acc_data, timeout=3600)
            cache.set(f'prediction_results_acc_{uuid}', predicted_classes_acc.tolist(), timeout=3600)
            logger.debug(f"Stored acc_data in cache: {cache.get(f'acc_data_storage_{uuid}')}")

            svm_acc_data = processed_data.loc['SVMacc'].tolist()
            logger.debug(f"SVMacc data to be sent: {svm_acc_data}")

            await self.send(text_data=json.dumps({
                'predictions': y_test_twelve_sec,
                'x_test_twelve_sec': x_test_twelve_sec.tolist(),
                'ppg_data': ppg_data,
                'acc_predictions': predicted_classes_acc.tolist(),
                'acc_data': acc_data,
                'svm_acc_data': svm_acc_data
            }))
            logger.info(f"Sent row ppg: {ppg_data}")

            channel_layer = get_channel_layer()
            await channel_layer.group_send(
                'receive_group',
                {
                    'type': 'sensor_data',
                    'data': json.dumps({
                        'x_test_twelve_sec': x_test_twelve_sec.tolist(),
                        'predictions': y_test_twelve_sec,
                        'ppg_data': ppg_data,
                        'acc_predictions': predicted_classes_acc.tolist(),
                        'acc_data': acc_data,
                        'svm_acc_data': svm_acc_data
                    })
                }
            )
            logger.info("Sent data to receive_group")


class ReceiveGroupConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'receive_group'
        try:
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
            logger.info(f"WebSocket connected to receive_group: {self.channel_name}")
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")

    async def disconnect(self, code):
        try:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            logger.info(f"WebSocket disconnected from receive_group: {self.channel_name}")
        except Exception as e:
            logger.error(f"WebSocket disconnection error: {e}")

    async def sensor_data(self, event):
        try:
            await self.send(event['data'])
            logger.info(f"Sent sensor data: {event['data']}")
        except Exception as e:
            logger.error(f"Error sending sensor data: {e}")
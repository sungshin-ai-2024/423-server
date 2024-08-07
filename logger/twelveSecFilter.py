import numpy as np
import heartpy as hp
import warnings
import logging
warnings.filterwarnings(action='ignore')

logger = logging.getLogger('logger')
window_size_green = 300
overlap = 30


class preprocessing:
    def __init__(self, data, overlap, chunk_size):
        self.data = data
        self.chunk_size = chunk_size
        self.overlap = overlap
        # 데이터 구조 확인을 위한 출력
        # print("data:", data)

    def chunk_data_hp(self):
        data_y = [y[0] for y in self.data]
        data_x = [x[1:] for x in self.data]
        flattened_data = [item for sublist in data_x for item in sublist]
        y_result=[data_y[0] for _ in flattened_data]
        sum_removed = 0
        pk_list = []

        filtered = hp.filter_signal(flattened_data, [0.5, 8], sample_rate=25, order=3,filtertype='bandpass')
        try:
            wd, m = hp.process(filtered, sample_rate=25)
            if (len(wd['peaklist']) != 0):
                sum_removed += len(wd['removed_beats'])  # 빨강색 피크
                x_result = wd['hr']  # bandpass를 통과한 chunk, 즉 300개의 신호
                temp_pk = (len(wd['peaklist']) - len(wd['removed_beats']))  # 초록색 피크의 개수
            else:
                temp_pk = 0
                temp = wd['hr']
                x_result = temp
        except:
            print("판단불가. ")

        pk_list.append(temp_pk)
        pk_np = np.array(pk_list)
        return x_result, y_result

    def dividing_and_extracting(self):
        print("dividing extracting 진입")
        x, y = self.chunk_data_hp()
        peak_shapes = []
        fake_index = []
        print("x: ", x)
        print("y: ", y)
        wd, m = hp.process(x, sample_rate=25)

        peaks = wd['peaklist']
        print("Peaks:", peaks)
        fake_peaks = wd['removed_beats']
        print("Fake Peaks:", fake_peaks)
        fake_index.extend(fake_peaks)
        real_peaks = [item for item in peaks if item not in fake_peaks]

        for index in real_peaks:
            if not ((index - 13 < 0) or (index + 14 >= len(x))):
                peak_shape = x[index - 13:index + 14]
                peak_shape = np.concatenate((np.array([y[0]]), peak_shape))  # y[0] 사용
                peak_shapes.append(peak_shape)

        np_peak = np.array(peak_shapes)
        print(np_peak.shape)
        return np_peak, x, y


class GMM_model_twelve_sec:
    def __init__(self, data, gmm_p, gmm_n, lab0, lab1, m, n):
        self.data = data
        self.gmm_p = gmm_p
        self.gmm_n = gmm_n
        self.lab0 = lab0
        self.lab1 = lab1
        self.m = m
        self.n = n

    def GMM_model(self):
        logger.debug("DEBUG: Entered GMM_model method")

        if self.gmm_p is None or self.gmm_n is None:
            raise ValueError("GMM models must be provided for test data")

        d = np.array(self.data)
        logger.debug(f"Input data shape: {d.shape}")
        logger.debug(f"Input data: {d}")

        dy = d[:, 0]
        d = d[:, 1:]
        logger.debug(f"Shape of d after slicing: {d.shape}")
        logger.debug(f"Shape of dy: {dy.shape}")

        tst = []

        lb1 = self.gmm_n.predict(d)
        lb2 = self.gmm_p.predict(d)
        logger.debug(f"Predictions from gmm_n: {lb1}")
        logger.debug(f"Predictions from gmm_p: {lb2}")

        for i in range(len(lb1)):
            if lb1[i] != self.lab1 and lb2[i] != self.lab0:
                pass
            else:
                tst.append(d[i])

        logger.debug(f"Filtered data tst shape: {np.array(tst).shape}")
        logger.debug(f"Filtered data tst: {tst}")

        normalized = []
        for value in tst:
            normalized_num = (value - self.n) / (self.m - self.n)
            normalized.append(normalized_num)

        data = np.array(normalized)
        data_x = data
        data_y = dy
        logger.debug(f"Normalized data shape: {data_x.shape}")
        logger.debug(f"Normalized data: {data_x}")
        logger.debug(f"Data_y shape: {data_y.shape}")
        logger.debug(f"Data_y: {data_y}")

        return data_x, data_y

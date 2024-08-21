import numpy as np
import heartpy as hp
import csv
import warnings
warnings.filterwarnings(action='ignore')
import read
import glob
from sklearn.model_selection import train_test_split
from sklearn.mixture import GaussianMixture
import pickle

window_size_green = 300
overlap = 30

class preprocessing:
    def __init__(self, data, train_or_test, overlap, chunk_size):
        self.data=data
        self.chunk_size=chunk_size
        self.tot=train_or_test
        self.overlap=overlap

    def chunk_data_hp(self):
        #global x_result
        """
            입력 데이터를 청크(300)로 나누고 HeartPy 라이브러리를 사용하여 bandpass filter를 거쳐 심박수(HR) 특징을 추출합니다.
        """
        data_y=[y[0] for y in self.data]
        data_x=[x[1:] for x in self.data]
        sum_removed=0
        y_result = []
        x_new_result=[]
        y_new_result=[]
        pk_list = []
        sum = 0
        cnt = 0
        exc = 0
        x_result=None
        for sublist, label in zip(data_x, data_y):
            for i in range(0, len(sublist) - self.chunk_size + 1, self.chunk_size - self.overlap):
                x_chunk = sublist[i:i + self.chunk_size]
                filtered = hp.filter_signal(x_chunk, [0.5, 8], sample_rate=25, order=3,
                                            filtertype='bandpass')
                try: # chunk의 전처리 후 process 함수가 실행이 안되는 경우가 꽤나 많아, 에러 표시로 인한 코드 실행 중지를 방지하기 위해 try except 문으로 구현
                    wd, m = hp.process(filtered, sample_rate=25)

                    """PPG 신호 피크가 존재하는 데이터에 대해서 빨갛게 표시된 피크들을 제거하고, 심박수 특징 추출"""
                    if (len(wd['peaklist']) != 0):
                        sum += (len(wd['peaklist']) - len(wd['removed_beats'])) #초록색 피크들의 총 합 계산(평균을 내기 위해)
                        sum_removed += len(wd['removed_beats']) #빨강색 피크
                        temp = wd['hr'] #bandpass를 통과한 chunk, 즉 300개의 신호
                        # print(temp)
                        temp_pk = (len(wd['peaklist']) - len(wd['removed_beats'])) #초록색 피크의 개수
                        if (cnt == 0):
                            x_result = temp
                        else:
                            x_result = np.vstack([x_result, temp]) #x_result는 모든 전처리된 300의 신호의 모음
                    else:
                        exc += 1
                        temp_pk = 0
                        temp = wd['hr']
                        if (cnt == 0):
                            x_result = temp
                        else:
                            x_result = np.concatenate((x_result, temp))
                    cnt += 1
                    pk_list.append(temp_pk)
                    y_result.append(label)
                except:
                    print("예외처리")
                    continue
        pk_np = np.array(pk_list)
        print(x_result.shape)
        print(pk_np.shape)
        print("cnt: ", cnt)
        print('exc: ', exc)
        print("y result: ", len(y_result))

        new_temp = 0
        new_cnt = 0
        """ 트레인 데이터의 경우 bpm 평균을 구함 """
        if(self.tot=="train"):
            for j in range(cnt):
                x_new_result.append(x_result[j])
                y_new_result.append(y_result[j])
                new_temp += m['bpm']
                new_cnt += 1
            new_avg = new_temp / new_cnt
            print("heartpy 평균: ", new_avg)
            print("cnt: ", cnt)
            print('exc: ', exc)
            print("필터링 후 데이터셋 개수: ", len(x_new_result))
            print("y result: ", len(y_new_result))
            print(sum_removed)
            return x_new_result, y_new_result
        elif(self.tot=="test"):
            return x_result, y_result
    def dividing_and_extracting(self):
        x,y=self.chunk_data_hp()
        peak_shapes = []
        fake_index = []
        # 각 청크의 최대값이 14000 이상인 인덱스를 데이터에서 제거 -> 가짜 피크
        index = np.where(np.max(x, axis=1) >= 14000)[0]  # >= 14000, 알아서 자르는 수 조정
        new_data = np.delete(x, index, axis=0)
        new_data_y=np.delete(y, index, axis=0)

        fake_index.extend(index)
        # l = len(index)
        for i in range(len(new_data)):
            temp = new_data[i, :]
            temp_y=new_data_y[i]
            wd, m = hp.process(temp, sample_rate=25) # HeartPy로 신호 처리

            peaks = wd['peaklist']  # 피크 리스트
            fake_peaks = wd['removed_beats']  # 제거된 피크 리스트
            fake_index.extend(fake_peaks)
            real_peaks = [item for item in peaks if item not in fake_peaks] # 실제 피크만 추출
            for index in real_peaks:
                if not ((index - 13 < 0) or (index + 14 >= new_data.shape[1])): # 실제 피크 주변 27개의 신호를 포함할 수 있는지 확인
                    peak_shape = temp[index - 13:index + 14] # 피크 주변 27 포인트 추출 -> 싱글펄스 (1.1초)
                    peak_shape = np.concatenate((np.array([temp_y]), peak_shape))
                    peak_shapes.append(peak_shape)

        np_peak = np.array(peak_shapes)
        print(np_peak.shape)
        return np_peak

    def GMM_model(self, tot, gmm_p=None, gmm_n=None):
        if tot == "train":
            data = self.dividing_and_extracting()
            print(np.shape(data))
            data0 = data[data[:, 0] == 0]
            data0 = data0[:, 1:]
            data1 = data[data[:, 0] == 1]
            data1 = data1[:, 1:]

            n_components = 2
            # 긍정적인 클래스에 대한 GMM 모델 학습
            gmm_p = GaussianMixture(n_components=n_components, covariance_type='full')
            gmm_p.fit(data0)

            # 긍정적인 클래스의 이상치 및 정상 데이터 분리
            labels = gmm_p.predict(data0)
            outliers = data0[labels == 1]
            normals = data0[labels == 0]

            # 부정적인 클래스에 대한 GMM 모델 학습
            gmm_n = GaussianMixture(n_components=n_components, covariance_type='full')
            gmm_n.fit(data1)
            labels = gmm_n.predict(data1)
            outliers_n = data1[labels == 1]
            normals_n = data1[labels == 0]

            global lab1
            global lab0

            # 각 클래스의 이상치와 정상 데이터의 평균을 비교하여 라벨 설정
            # 부정데이터의 경우 평균이 더 큰 lable이 대표값으로 선정되고,
            # 긍정데이터의 경우 평균이 더 작은 lable이 대표값으로 선정됨
            # 그에따라 lab0, lab1이 정해짐
            if np.mean(normals_n) > np.mean(outliers_n):
                spp1 = normals_n
                lab1 = 0
            else:
                spp1 = outliers_n
                lab1 = 1
            if np.mean(normals) < np.mean(outliers):
                spp0 = normals
                lab0 = 0
            else:
                spp0 = outliers
                lab0 = 1

            global m
            global n
            m = np.max(spp1) #전체 데이터에서의 최대값
            n = np.min(spp1) #전체 데이터에서의 최소값
            # normalilzation 하는 부분
            normalized_train = []
            for value in spp0:
                normalized_num = (value - n) / (m - n)
                normalized_train.append(normalized_num)
            normalized_train_n = []
            for value in spp1:
                normalized_num = (value - n) / (m - n)
                normalized_train_n.append(normalized_num)

            normalized_train = np.array(normalized_train)
            normalized_train_n = np.array(normalized_train_n)

            normals_y = np.zeros((normalized_train.shape[0], 1))
            g_x_p = np.concatenate((normals_y, normalized_train), axis=1)
            normals_n_y = np.ones((normalized_train_n.shape[0], 1))
            g_x_n = np.concatenate((normals_n_y, normalized_train_n), axis=1)

            data = np.concatenate((g_x_p, g_x_n))
            np.random.shuffle(data)
            data_x = data[:, 1:]
            data_y = data[:, 0]

            x_train_g, x_test_g, y_train_g, y_test_g = train_test_split(data_x, data_y, test_size=0.2)
            return x_train_g, x_test_g, y_train_g, y_test_g, gmm_p, gmm_n, lab0, lab1, m, n


        elif tot == "test":

            with open("../Emotion-Classification/list.pickle", "rb") as fi:

                test = pickle.load(fi)

            lab0_f = test[0]

            lab1_f = test[1]

            m_f = test[2]

            n_f = test[3]

            if gmm_p is None or gmm_n is None:
                raise ValueError("GMM models must be provided for test data")

            data = self.dividing_and_extracting()

            d = np.array(data)

            dy = d[:, 0]

            d = d[:, 1:]

            tst = []

            # GMM 모델을 사용하여 테스트 데이터의 라벨 예측 (긍정, 부정 모두)

            lb1 = gmm_n.predict(d)

            lb2 = gmm_p.predict(d)

            # 라벨이 lab1, lab2 중 하나라도 맞는 것이 없으면 이상치로 판단하여 제거

            # 즉, 테스트데이터가 gmm 모델에 적용되어 긍정 모델과 부정 모델 중 하나라도 맞지 않으면 pass됨

            for i in range(len(lb1)):

                if lb1[i] != lab1_f and lb2[i] != lab0_f:

                    pass

                else:

                    tst.append(d[i])

            # 정규화 과정

            normalized = []

            for value in tst:
                normalized_num = (value - n_f) / (m_f - n_f)

                normalized.append(normalized_num)

            data = np.array(normalized)

            data_x = data

            data_y = dy

            return data_x, data_y

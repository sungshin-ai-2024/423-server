# import CNN_model
import glob
import filter
import twelveSecFilter
import twelveSecPlot
import read
import numpy as np
# import test_plot
# import heartpy as hp
# import matplotlib.pyplot as plt
# import tensorflow as tf

chunk_size = 300
overlap = 0

file_positive_green = glob.glob(r"P\green\*.txt")
file_negative_green = glob.glob(r"N\green\*.txt")
model_path = "best_model.h5"
twelveSec = glob.glob("12sec.txt")

# 데이터 읽기
train_positive_reader = read.read(data=file_positive_green, y=0, chunk_size=chunk_size, overlap=overlap)
train_negative_reader = read.read(data=file_negative_green, y=1, chunk_size=chunk_size, overlap=overlap)
p_train_list = train_positive_reader.read_txt_files_with_skip()
n_train_list = train_negative_reader.read_txt_files_with_skip()
train_list = p_train_list + n_train_list

# 데이터 전처리
train_filtered = filter.preprocessing(data=train_list, chunk_size=chunk_size, train_or_test="train", overlap=overlap)
x_train, x_test, y_train, y_test, gmm_p, gmm_n, lab0, lab1, m, n = train_filtered.GMM_model(tot="train")


# 테스트 데이터 읽기 및 전처리
test_data = read.read(twelveSec, 1, chunk_size=chunk_size, overlap=overlap)
test_data_list = test_data.read_txt_files_with_skip()
print(f"DEBUG: test_data_list (first 5 entries): {test_data_list[:5]}")  # 첫 5개 데이터 확인
# 테스트 데이터 전처리
test_filtered = twelveSecFilter.preprocessing(data=test_data_list, chunk_size=chunk_size, overlap=overlap)
twelve_sec_filtered, twelve_sec_x, twelve_sec_y = test_filtered.dividing_and_extracting()

# 전처리된 데이터 형태 출력
print(f"DEBUG: Shape of twelve_sec_filtered: {np.array(twelve_sec_filtered).shape}")
print(f"DEBUG: Shape of twelve_sec_x: {np.array(twelve_sec_x).shape}")
print(f"DEBUG: Shape of twelve_sec_y: {np.array(twelve_sec_y).shape}")

# 모델 적용
model_for_twelve_sec = twelveSecFilter.GMM_model_twelve_sec(twelve_sec_filtered, gmm_p, gmm_n, lab0, lab1, m, n)
x_test_twelve_sec, y_test_twelve_sec = model_for_twelve_sec.GMM_model()

# 모델 적용 결과 출력
print(f"DEBUG: Shape of x_test_twelve_sec: {np.array(x_test_twelve_sec).shape}")
print(f"DEBUG: Shape of y_test_twelve_sec: {np.array(y_test_twelve_sec).shape}")

# 예측 수행
predictor = twelveSecPlot.PeakPredictor(model_path, x_test_twelve_sec)
y_test_twelve_sec = predictor.plot_peaks()

# 예측 결과 출력
print(f"DEBUG: Predicted y_test_twelve_sec: {y_test_twelve_sec}")

# 27개의 벡터로 이루어진 피크를 보려면 x_test_twelve_sec
# 이 피크들의 예측값을 보려면 y_test_twelve_sec


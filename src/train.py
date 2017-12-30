import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from keras.callbacks import ReduceLROnPlateau
from pandas import datetime, Series
import math, time
import itertools
from sklearn import preprocessing
from sklearn.preprocessing import MinMaxScaler
import datetime
from operator import itemgetter
from sklearn.metrics import mean_squared_error
from math import sqrt
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation
from keras.layers.recurrent import LSTM

scaler = MinMaxScaler(feature_range=(0, 1))

def get_stock_data(stock_name, normalized=0):
    url="data/0883.HK.csv"

    col_names = ['Date','Open','High','Low','Close','Adj close', 'Volume']
    stocks = pd.read_csv(url, header=0, names=col_names)[['Open','Low','High','Volume','Close', 'Close']]
    # Read the Close column twice and shift it down by 1 so that each row has a previous close price except the first one
    stocks.columns = ['Open','Low','High','Volume','PrevClose', 'Close']
    stocks.PrevClose = stocks.PrevClose.shift(1)
    # set the first PrevClose to be the current Close as it is a NaN after the shift
    stocks.PrevClose[0] = stocks.Close[0]

    # Combine all columns into 1 by this fomular
    # (EachPrice - PrevClose) * volume
    params = []
    print(len(stocks))
    for index in range(len(stocks) - 1):
        param = ((stocks.Open[index] - stocks.PrevClose[index]) / stocks.PrevClose[index] * stocks.Volume[index]
                 + (stocks.Low[index] - stocks.PrevClose[index]) / stocks.PrevClose[index]  * stocks.Volume[index]
                 + (stocks.High[index] - stocks.PrevClose[index]) / stocks.PrevClose[index] * stocks.Volume[index]
        )
        if (math.isnan(param)) or param < 0:
            param = 0.0

        param = float(param)
        params.append([float(param), stocks.Close[index]])

    print(params)
    # normalize features
    scaled = scaler.fit_transform(params)
    print(scaled)
    df = pd.DataFrame(scaled)
    # df.drop(df.columns[[0,3,5]], axis=1, inplace=True)
    return df

stock_name = '0883'
df = get_stock_data(stock_name,0)
df.tail()

today = datetime.date.today()
file_name = "train.csv"
df.to_csv(file_name)

def load_data(stock, seq_len):
    amount_of_features = len(stock.columns)
    print('amount of features: ', amount_of_features)
    data = stock.as_matrix() #pd.DataFrame(stock)
    sequence_length = seq_len + 1
    result = []
    for index in range(len(data) - sequence_length):
        result.append(data[index: index + sequence_length])


    result = np.array(result)
    
    row = round(0.9 * result.shape[0])
    train = result[:int(row), :]
    x_train = train[:, :-1]
    y_train = train[:, -1][:,-1]   
    x_test = result[int(row):, :-1]
    y_test = result[int(row):, -1][:,-1]
    print("the training Y values")
    print(y_train)

    x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], amount_of_features))
    x_test = np.reshape(x_test, (x_test.shape[0], x_test.shape[1], amount_of_features))  

    return [x_train, y_train, x_test, y_test]

def build_model(layers):
    model = Sequential()

    model.add(LSTM(
        input_dim=layers[0],
        output_dim=layers[1],
        return_sequences=True))
    model.add(Dropout(0.2))

    model.add(LSTM(
        layers[2],
        return_sequences=False))
    model.add(Dropout(0.2))

    model.add(Dense(
        output_dim=layers[2]))
    model.add(Activation("linear"))

    start = time.time()
    model.compile(loss="mse", optimizer="rmsprop",metrics=['accuracy'])
    print("Compilation Time : ", time.time() - start)
    return model

def build_model2(layers):
    d = 0.2
    model = Sequential()
    model.add(LSTM(128, input_shape=(layers[1], layers[0]), return_sequences=True))
    model.add(Dropout(d))
    model.add(LSTM(64, input_shape=(layers[1], layers[0]), return_sequences=False))
    model.add(Dropout(d))
    model.add(Dense(16,init='uniform',activation='relu'))
    model.add(Dense(1,init='uniform',activation='relu'))
    model.compile(loss='mse',optimizer='adam',metrics=['accuracy'])
    return model

window = 5
X_train, y_train, X_test, y_test = load_data(df[::-1], window)
print("X_train", X_train.shape)
print("y_train", y_train.shape)
print("X_test", X_test.shape)
print("y_test", y_test.shape)

# model = build_model([3,lag,1])
numOfColumnsAsInout = 2
model = build_model2([numOfColumnsAsInout,window,1])
print(model.summary())

normalizationFactor = 10

# callbacks
lr_reducer = ReduceLROnPlateau(monitor='val_loss', patience=50, cooldown=0, verbose=1)

model.fit(
    X_train/normalizationFactor,
    y_train/normalizationFactor,
    batch_size=64,
    nb_epoch=200,
    validation_data=(X_test, y_test), callbacks=[lr_reducer],
    verbose=1)

trainScore = model.evaluate(X_train, y_train, verbose=1)
print('Train Score: %.2f MSE (%.2f RMSE)' % (trainScore[0], math.sqrt(trainScore[0])))

testScore = model.evaluate(X_test, y_test, verbose=1)
print('Test Score: %.2f MSE (%.2f RMSE)' % (testScore[0], math.sqrt(testScore[0])))

# print(X_test[-1])
diff=[]
ratio=[]
p = model.predict(X_test)
for u in range(len(y_test)):
    pr = p[u][0]
    ratio.append((y_test[u]/pr)-1)
    diff.append(abs(y_test[u]- pr))
    #print(u, y_test[u], pr, (y_test[u]/pr)-1, abs(y_test[u]- pr))

import matplotlib.pyplot as plt2

plt2.plot(p,color='red', label='prediction')
plt2.plot(y_test,color='blue', label='y_test')
plt2.legend(loc='upper left')
plt2.show()
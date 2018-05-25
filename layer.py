"""
layer.py

experimental nn network

doesnt work at all

by Alexander Liao
"""

from keras.layers import Input, Dense, Dropout
from keras.models import Model, Sequential
from keras import regularizers
import numpy
from scipy.io import loadmat
import tensorflow as tf
from sklearn.preprocessing import normalize, scale
from sklearn.metrics import r2_score
from datetime import datetime

# fix random seed for reproducibility
numpy.random.seed(7)
X=numpy.loadtxt('feature.csv',dtype='float',delimiter=',')
Y=numpy.loadtxt('label.csv',dtype='float',delimiter=',')
Xtrain=X[1:5000,:]
Ytrain=Y[1:5000,1]
#Xtrain=normalize(Xtrain,axis=0)
Xtrain = scale( Xtrain, axis=0, with_mean=True, with_std=True, copy=True )
#Ytrain=normalize(Ytrain,axis=0)
Ytrain = scale( Ytrain, axis=0, with_mean=True, with_std=True, copy=True )
print(Xtrain)
Xtest=X[300000:310000,:]
Ytest=Y[300000:310000,1]
#Xtest=normalize(Xtest,axis=0)
Xtest = scale( Xtest, axis=0, with_mean=True, with_std=True, copy=True )
#Ytest=normalize(Ytest,axis=0)
Ytest = scale( Ytest, axis=0, with_mean=True, with_std=True, copy=True )
print(type(X))
print(type(Y))

def nn_1(input_length):
    input_layer = Input(shape=(input_length,))
    encoded = Dense(256, activation="tanh")(input_layer)

    encoded = Dense(256, activation="tanh" )(encoded)
    encoded = Dropout(0.1, noise_shape=None, seed=None)(encoded)
    encoded = Dense(256, activation="tanh" )(encoded)
    encoded = Dense(256, activation="tanh" )(encoded)
    encoded = Dropout(0.1, noise_shape=None, seed=None)(encoded)
    encoded = Dense(256, activation="tanh" )(encoded)

    encoded = Dense(256, activation="tanh")(encoded)
    encoded = Dense( 256, activation="tanh")(encoded)
    encoded = Dense(256, activation="tanh")(encoded)
    encoded = Dense( 256, activation="tanh")(encoded)

    encoded = Dense(256, activation="tanh")(encoded)
    encoded = Dense( 256, activation="tanh")(encoded)
    encoded = Dense(256, activation="tanh")(encoded)
    encoded = Dense( 256, activation="tanh")(encoded)

    decoded = Dense(256, activation="tanh" )(encoded)
    encoded = Dropout(0.1, noise_shape=None, seed=None)(encoded)
    decoded = Dense(256, activation="tanh" )(decoded)
    encoded = Dropout(0.1, noise_shape=None, seed=None)(encoded)
    decoded = Dense(256, activation="relu" )(decoded)

    decoded = Dense(1, activation="linear")(decoded)
    # encoder = Model(input_layer, encoded)
    nn_predictor = Model(input_layer, decoded)
    nn_predictor.compile(optimizer="adam", loss="mean_squared_error")  # mean_absolute_error ?
    return nn_predictor

nn_predictor = nn_1(3)

with tf.device('/gpu:0'):
    try:
        nn_predictor.fit(Xtrain,Ytrain, batch_size=512, epochs=500, validation_split=0.2,verbose=1)
    except (KeyboardInterrupt, SystemExit):
        nn_predictor.save(str(datetime.now()))
        print(r2_score(Ytest,nn_predictor.predict(Xtest)))
nn_predictor.save(str(datetime.now()))
print(r2_score(Ytest,nn_predictor.predict(Xtest)))

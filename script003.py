"""
script003.py

continue with hidden space strategy
important: error analysis by parts

current experiment: tc_cols --> pc_cols --> (DBSCAN) track_id

by Tianyi Miao
"""

import numpy as np
import pandas as pd

import itertools

from sklearn.cluster import DBSCAN, Birch, AgglomerativeClustering, KMeans, MiniBatchKMeans
from sklearn.preprocessing import StandardScaler, LabelEncoder
import hdbscan

from keras.layers import Input, Dense
from keras.models import Model, Sequential

from trackml.dataset import load_event
from trackml.score import score_event

from arsenal import get_directories, get_event_name, StaticFeatureEngineer
from arsenal import HITS, CELLS, PARTICLES, TRUTH


# define important directories; change it if you store your data differently!
# type help(get_directories) for more information
# TRAIN_DIR, TEST_DIR, DETECTORS_DIR, SAMPLE_SUBMISSION_DIR, TRAIN_EVENT_ID_LIST, TEST_EVENT_ID_LIST = get_directories("E:/TrackMLData/")
TRAIN_DIR, TEST_DIR, DETECTORS_DIR, SAMPLE_SUBMISSION_DIR, TRAIN_EVENT_ID_LIST, TEST_EVENT_ID_LIST = get_directories()


n_event = 10  # TODO: important parameter
n_train = 10  # TODO: important parameter
event_id_list = np.random.choice(TRAIN_EVENT_ID_LIST, size=n_event, replace=False)
train_id_list = event_id_list[:n_train]  # training set
val_id_list = event_id_list[n_train:]  # validation set


# c is short for generic x/y/z
c_cols = ["x", "y", "z"]
vlm_cols = ["volume_id", "layer_id", "module_id"]
vc_cols = ["vx", "vy", "vz"]
pc_cols = ["px", "py", "pz"]
tc_cols = ["tx", "ty", "tz"]
tpc_cols = ["tpx", "tpy", "tpz"]

feature_cols = tc_cols  # TODO: important parameter


# load neural network
def get_nn_1():
    input_layer = Input(shape=(len(feature_cols),))
    encoded = Dense(64, activation="relu")(input_layer)
    encoded = Dense(64, activation="relu")(encoded)
    encoded = Dense(64, activation="tanh")(encoded)
    encoded = Dense(64, activation="tanh")(encoded)

    decoded = Dense(64, activation="tanh")(encoded)
    decoded = Dense(64, activation="tanh")(decoded)
    decoded = Dense(64, activation="relu")(decoded)
    decoded = Dense(len(pc_cols), activation="linear")(decoded)
    # encoder = Model(input_layer, encoded)
    nn_predictor = Model(input_layer, decoded)
    nn_predictor.compile(optimizer="adadelta", loss="mean_squared_error")
    return nn_predictor


def get_nn_2(input_length):
    input_layer = Input(shape=(input_length,))
    encoded = Dense(64, activation="relu")(input_layer)
    encoded = Dense(96, activation="relu")(encoded)
    encoded = Dense(64, activation="relu")(encoded)
    encoded = Dense(96, activation="relu")(encoded)
    encoded = Dense(64, activation="relu")(encoded)
    encoded = Dense(96, activation="relu")(encoded)
    encoded = Dense(64, activation="relu")(encoded)
    encoded = Dense(96, activation="relu")(encoded)

    decoded = Dense(64, activation="relu")(encoded)
    decoded = Dense(96, activation="relu")(decoded)
    decoded = Dense(96, activation="relu")(decoded)
    decoded = Dense(len(pc_cols), activation="linear")(decoded)
    # encoder = Model(input_layer, encoded)
    nn_predictor = Model(input_layer, decoded)
    nn_predictor.compile(optimizer="adadelta", loss="mean_squared_error")  # mean_absolute_error ?
    return nn_predictor


def preprocess_1(df):
    r = np.sqrt(df.tx ** 2 + df.ty ** 2 + df.tz ** 2)
    rz = np.sqrt(df.tx ** 2 + df.ty ** 2)
    df["tx"] /= r
    df["ty"] /= r
    df["tz"] /= rz
    return df


nn_predictor = get_nn_2(3)  # TODO: important parameter


def test_dbscan(eps_list, hit_id, data, scaling):
    for eps in eps_list:
        dbscan_1 = DBSCAN(eps=eps, min_samples=1, algorithm='auto', n_jobs=-1)
        pred = pd.DataFrame({
            "hit_id": hit_id,
            "track_id": dbscan_1.fit_predict(
                StandardScaler().fit_transform(data) if scaling else data
            )
        })
        print("eps={}, score:  ".format(eps), end='\t')
        print(score_event(truth=truth, submission=pred))


def test_agglomerative(n_clusters, hit_id, data, scaling):
    ac = AgglomerativeClustering(n_clusters=n_clusters, affinity="euclidean", linkage="average")
    pred = pd.DataFrame({
        "hit_id": hit_id,
        "track_id": ac.fit_predict(
            StandardScaler().fit_transform(data) if scaling else data
        )
    })
    print("Agglomerative Clustering score:  ", end="\t")
    print(score_event(truth=truth, submission=pred))


def test_birch(threshold_list, n_clusters, hit_id, data, scaling):
    for t in threshold_list:
        birch_1 = Birch(threshold=t, branching_factor=50, n_clusters=n_clusters, copy=True)
        pred = pd.DataFrame({
            "hit_id": hit_id,
            "track_id": birch_1.fit_predict(
                StandardScaler().fit_transform(data) if scaling else data
            )
        })
        print("Birch score (threshold={}):  ".format(t), end="\t")
        print(score_event(truth=truth, submission=pred))


def test_kmeans(n_clusters, hit_id, data, scaling, minibatch):
    km = MiniBatchKMeans(n_clusters=n_clusters) if minibatch else KMeans(n_clusters=n_clusters)
    pred = pd.DataFrame({
        "hit_id": hit_id,
        "track_id": km.fit_predict(
            StandardScaler().fit_transform(data) if scaling else data
        )
    })
    print("KMeans score:  ", end="\t")
    print(score_event(truth=truth, submission=pred))


for event_id in train_id_list:
    print('='*120)
    particles, truth = load_event(TRAIN_DIR + get_event_name(event_id), [PARTICLES, TRUTH])
    truth = truth.merge(particles, how="left", on="particle_id", copy=False)

    # change tc_cols features
    preprocess_1(truth)  # TODO: important procedure
    print("directly cluster on tx/ty/tc before dropping noisy hits:")
    # test_dbscan((0.001, 0.003, 0.01, 0.03, 0.1), truth.hit_id, truth[tc_cols], scaling=True)
    # test_agglomerative(np.unique(truth.particle_id).size, truth.hit_id, truth[tc_cols], scaling=False)
    # test_birch((0.1, 0.05, 0.02), np.unique(truth.particle_id).size, truth.hit_id, truth[tc_cols], scaling=False)
    test_kmeans(n_clusters=np.unique(truth.particle_id).size,
                hit_id=truth.hit_id, data=truth[tc_cols],
                scaling=False, minibatch=False)

    # drop noisy hits
    noisy_indices = truth[truth.particle_id == 0].index
    truth.drop(noisy_indices, axis=0, inplace=True)  # drop noisy hits

    # drop useless columns
    truth.drop(vc_cols + ["q", "nhits"], axis=1, inplace=True)

    print("directly cluster on tx/ty/tz after dropping noisy hits:")
    # test_dbscan((0.001, 0.003, 0.01, 0.03, 0.1), truth.hit_id, truth[tc_cols], scaling=True)
    # test_agglomerative(np.unique(truth.particle_id).size, truth.hit_id, truth[tc_cols], scaling=False)
    # test_birch((0.1, 0.05, 0.02), np.unique(truth.particle_id).size, truth.hit_id, truth[tc_cols], scaling=False)
    test_kmeans(n_clusters=np.unique(truth.particle_id).size,
                hit_id=truth.hit_id, data=truth[tc_cols],
                scaling=False, minibatch=False)

    print("cluster on true px/py/pz:")
    # test_dbscan((0.001, 0.003, 0.01, 0.03, 0.1), truth.hit_id, truth[pc_cols], scaling=True)
    # test_agglomerative(np.unique(truth.particle_id).size, truth.hit_id, truth[pc_cols], scaling=False)
    # test_birch((0.1, 0.05, 0.02), np.unique(truth.particle_id).size, truth.hit_id, truth[pc_cols], scaling=False)
    test_kmeans(n_clusters=np.unique(truth.particle_id).size,
                hit_id=truth.hit_id, data=truth[pc_cols],
                scaling=False, minibatch=False)

    # current experiment: tc_cols to pc_cols
    nn_predictor.fit(x=truth[feature_cols],
                     y=truth[pc_cols],
                     batch_size=256, epochs=20, shuffle=True, validation_split=0.2,
                     verbose=0
                     )

    # checck whether underfitting
    X_new = nn_predictor.predict(x=truth[feature_cols], verbose=0)
    # print(pd.DataFrame(X_new).describe()); print(truth[pc_cols].describe())
    print("cluster with results from neural networks")
    # test_dbscan((0.001, 0.003, 0.01, 0.03, 0.1), truth.hit_id, X_new, scaling=True)
    # test_agglomerative(np.unique(truth.particle_id).size, truth.hit_id, X_new, scaling=False)
    # test_birch((0.1, 0.05, 0.02), np.unique(truth.particle_id).size, truth.hit_id, X_new, scaling=False)
    test_kmeans(n_clusters=np.unique(truth.particle_id).size,
                hit_id=truth.hit_id, data=X_new,
                scaling=False, minibatch=False)

exit("early exit before running on the validation set")
"""
for event_id in val_id_list:
    print("start predicting new event")
    particles, truth = load_event(TRAIN_DIR + get_event_name(event_id), [PARTICLES, TRUTH])

    noisy_indices = truth[truth.particle_id == 0].index
    truth.drop(noisy_indices, axis=0, inplace=True)  # drop noisy hits

    truth = truth.merge(particles, how="left", on="particle_id", copy=False)
    X_new = nn_predictor.predict(x=truth[feature_cols], verbose=1)

    for eps in (1e-3, 3e-3, 1e-2, 3e-2, 0.1, 0.3):
        # eps = 0.00715
        dbscan_1 = DBSCAN(eps=eps, min_samples=1, algorithm='auto', n_jobs=-1)
        pred = pd.DataFrame({
            "hit_id": truth.hit_id,
            "track_id": dbscan_1.fit_predict(X_new)
        })
        print("eps={}, final score:".format(eps), end="    ")
        print(score_event(truth=truth, submission=pred))
"""
"""
for event_id in train_id_list:
    # important observation:
    # Many particle_id in particles do not appear in truth; perhaps they are not detected at all
    # One particle_id in truth does not appear in particles: 0.

    hits, particles, truth = load_event(TRAIN_DIR + get_event_name(event_id), [HITS, PARTICLES, TRUTH])
    noisy_indices = truth[truth.particle_id == 0].index
    hits.drop(noisy_indices, axis=0, inplace=True)  # drop noisy hits
    truth.drop(noisy_indices, axis=0, inplace=True)  # drop noisy hits

    truth = truth.merge(particles, how="left", on="particle_id", copy=False)
    # TODO: drop useless columns==================
    truth.drop(tc_cols + tpc_cols, axis=1, inplace=True)
    hits.drop(c_cols + vlm_cols, axis=1, inplace=True)
    # TODO: ======================================
    X_new = truth[pc_cols]

    # categorical encoding: use LabelEncoder

    print("categorical encoding score:    ", end="")
    pred = pd.DataFrame({
        "hit_id": hits.hit_id,
        "track_id": LabelEncoder().fit_transform([str(row) for row in X_new.values])
        # "track_id": truth.particle_id
    })
    print(score_event(truth=truth, submission=pred))

    use_hdbscan = False
    print("start predicting...")
    if use_hdbscan:  # use DBSCAN instead
        for min_cluster_size in range(2, 10):
            dbscan_2 = hdbscan.HDBSCAN(min_samples=2, min_cluster_size=min_cluster_size, cluster_selection_method='leaf',
                                       prediction_data=False, metric='braycurtis', core_dist_n_jobs=-1)

            pred = pd.DataFrame({
                "hit_id": hits.hit_id,
                "track_id": dbscan_2.fit_predict(X_new)
            })
            print("n={}, final score:".format(min_cluster_size), end="    ")
            print(score_event(truth=truth, submission=pred))
    else:
        for eps in (1e-3, 1e-2, 1e-1, 1.0, 1e1, 1e2, 1e3, 1e4):
            # eps = 0.00715
            dbscan_1 = cluster.DBSCAN(eps=eps, min_samples=1, algorithm='auto', n_jobs=-1)
            pred = pd.DataFrame({
                "hit_id": hits.hit_id,
                "track_id": dbscan_1.fit_predict(X_new)
            })
            print("eps={}, final score:".format(eps), end="    ")
            print(score_event(truth=truth, submission=pred))
"""


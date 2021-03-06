import pickle
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.model_selection import cross_val_score
from fastsklearnfeature.interactiveAutoML.new_bench.multiobjective.metalearning.analyse.time_measure import get_recall
from fastsklearnfeature.interactiveAutoML.new_bench.multiobjective.metalearning.analyse.time_measure import time_score2
from fastsklearnfeature.interactiveAutoML.new_bench.multiobjective.metalearning.analyse.time_measure import get_avg_runtime
from fastsklearnfeature.interactiveAutoML.new_bench.multiobjective.metalearning.analyse.time_measure import get_optimum_avg_runtime

from sklearn.metrics import make_scorer
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn import tree
from sklearn.tree import export_graphviz
from subprocess import call
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.model_selection import GroupKFold
from sklearn.model_selection import RandomizedSearchCV
import copy
import glob
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
from tensorflow import keras

from tensorflow.keras import backend as K

from sklearn.preprocessing import OneHotEncoder


mappnames = {1:'var', 2: 'chi2', 3:'acc rank', 4: 'robust rank', 5: 'fair rank', 6: 'weighted ranking', 7: 'hyperopt', 8: 'evo'}

names = ['accuracy',
	 'fairness',
	 'k_rel',
	 'k',
	 'robustness',
	 'privacy',
	 'search_time',
	 'cv_acc - acc',
	 'cv_fair - fair',
	 'cv_k - k rel',
	 'cv_k - k',
	 'cv_robust - robust',
     'cv time',
	 'rows',
	 'columns']

def print_constraints_2(features):


	my_str = ''
	for i in range(len(names)):
		my_str += names[i] + ': ' + str(features[i]) + ' '
	print(my_str)


def print_strategies(results):
	print("all strategies failed: " + str(results[0]) +
		  "\nvar rank: " + str(results[1]) +
		  '\nchi2 rank: ' + str(results[2]) +
		  '\naccuracy rank: ' + str(results[3]) +
		  '\nrobustness rank: ' + str(results[4]) +
		  '\nfairness rank: ' + str(results[5]) +
		  '\nweighted ranking: ' + str(results[6]) +
		  '\nhyperparameter opt: ' + str(results[7]) +
		  '\nevolution: ' + str(results[8])
		  )


#logs_adult = pickle.load(open('/home/felix/phd/meta_learn/classification/metalearning_data_adult.pickle', 'rb'))
#logs_heart = pickle.load(open('/home/felix/phd/meta_learn/classification/metalearning_data_heart.pickle', 'rb'))



#get all files from folder

# list files "/home/felix/phd/meta_learn/random_configs_eval"
#all_files = glob.glob("/home/felix/phd/meta_learn/random_configs_eval_long/*.pickle")
#all_files = glob.glob("/home/felix/phd/meta_learn/random_configs_with_repair_optimization/*.pickle")
all_files = glob.glob("/home/felix/phd/meta_learn/combine_random_configs/*.pickle") #1hour
#all_files = glob.glob("/home/felix/phd/meta_learn/3h_configs/*.pickle") #1hour


dataset = {}
for afile in all_files:
	data = pickle.load(open(afile, 'rb'))
	for key in data.keys():
		if not key in dataset:
			dataset[key] = []
		dataset[key].extend(data[key])


print(dataset['best_strategy'])
print(len(dataset['best_strategy']))

print(dataset.keys())


#get maximum number of evaluations if a strategy is fastest
eval_strategies = []
for i in range(9):
	eval_strategies.append([])

print(eval_strategies)
for bests in range(len(dataset['best_strategy'])):
	current_best = dataset['best_strategy'][bests]
	if current_best > 0:
		eval_strategies[current_best].append(dataset['evaluation_value'][bests][current_best][0])

print(eval_strategies)

print("max evaluations:")
for i in range(9):
	if len(eval_strategies[i]) > 0:
		print(mappnames[i] + ' min evaluations: ' + str(np.min(eval_strategies[i])) + ' max evaluations: ' + str(np.max(eval_strategies[i])) + ' avg evaluations: ' + str(np.mean(eval_strategies[i])) + ' len evaluations: ' + str(len(eval_strategies[i])))











#print(logs_regression['features'])

my_score = make_scorer(time_score2, greater_is_better=False, logs=dataset)
my_recall_score = make_scorer(get_recall, logs=dataset)
my_runtime_score = make_scorer(get_avg_runtime, logs=dataset)
my_optimal_runtime_score = make_scorer(get_optimum_avg_runtime, logs=dataset)

X_train = dataset['features']
y_train = dataset['best_strategy']

meta_classifier = RandomForestClassifier(n_estimators=1000)
#meta_classifier = DecisionTreeClassifier(random_state=0, max_depth=3)
meta_classifier = meta_classifier.fit(X_train, np.array(y_train) == 0)
#meta_classifier = meta_classifier.fit(X_train, y_train)



'''
# Export as dot file
export_graphviz(meta_classifier, out_file='/tmp/tree.dot',
                feature_names = ['accuracy',
											  'fairness',
											  'k_rel',
											  'k',
											  'robustness',
											  'privacy',
											  'cv_acc - acc',
											  'cv_fair - fair',
											  'cv_k - k rel',
											  'cv_k - k',
											  'cv_robust - robust',
											  'rows',
											  'columns'],
                class_names = np.array(meta_classifier.classes_, dtype=str),#['nothing','var','chi2','acc rank','robust rank','fair rank','weighted ranking','hyperopt','evo'],#['success', 'failure'],
                rounded = True, proportion = False,
                precision = 2, filled = True)

call(['dot', '-Tpng', '/tmp/tree.dot', '-o', '/tmp/tree.png', '-Gdpi=600'])

plt.show()
'''



#meta_classifier = DummyClassifier(strategy="uniform")
#meta_classifier = DummyClassifier(strategy="most_frequent")
#meta_classifier = DummyClassifier(strategy="constant", constant=8)

#scores = cross_val_score(meta_classifier, X_train, np.array(y_train) == 0, cv=10, scoring='f1')
#print('did it fail: ' + str(np.mean(scores)))


success_ids = np.where(np.array(y_train) > 0)[0]
print(success_ids)


new_success_ids = []
for s_i in success_ids:
	delete_b = False
	for strategy_i in dataset['evaluation_value'][s_i].keys():
		if dataset['evaluation_value'][s_i][strategy_i][0] == 1:
			delete_b = True
			break
	if not delete_b:
		new_success_ids.append(s_i)

#success_ids = new_success_ids

print("training size: " + str(len(success_ids)))



#todo: balance by class

#print(X_train)
X_data = np.array(X_train)[success_ids]
y_data = np.array(y_train)[success_ids]
groups = np.array(dataset['dataset_id'])[success_ids]

outer_cv = list(GroupKFold(n_splits=4).split(X_data, y_data, groups=groups))

encoder = OneHotEncoder(sparse=False)
one_hot_labels = encoder.fit_transform(y_data.reshape(-1, 1))
print(encoder.categories_)
print(one_hot_labels.shape)

def get_runtime_for_fold_predictions(predictions, test_ids, categories):
	all_runtimes = []
	for p_i in range(len(predictions)):
		current_strategy = categories[predictions[p_i]]
		current_id = success_ids[test_ids[p_i]]
		if current_strategy in dataset['times_value'][current_id] and len(
				dataset['times_value'][current_id][current_strategy]) >= 1:
			all_runtimes.append(min(dataset['times_value'][current_id][current_strategy]))
		else:
			all_runtimes.append(dataset['features'][current_id][6])
	return all_runtimes

all_runtimes_in_cv_folds = []

for train_ids, test_ids in outer_cv:
	print("train_ids: " + str(train_ids))
	print("test_ids: " + str(test_ids))

	runtimes = np.zeros((len(train_ids), len(encoder.categories_[0])), dtype=np.float32)
	for c_i in range(len(encoder.categories_[0])):
		current_strategy = int(encoder.categories_[0][c_i])
		for p_i in range(len(train_ids)):
			current_id = success_ids[train_ids[p_i]]
			if current_strategy in dataset['times_value'][current_id] and len(
					dataset['times_value'][current_id][current_strategy]) >= 1:
				runtimes[p_i, c_i] = min(dataset['times_value'][current_id][current_strategy])
			else:
				runtimes[p_i, c_i] = dataset['features'][current_id][6]

	def customLoss(y_true, y_pred, **kwargs):
		WEIGHTS = tf.constant(value=runtimes, dtype=tf.float32)

		y = tf.sign(tf.reduce_max(y_pred, axis=-1, keepdims=True)-y_pred)
		y = (y-1)*(-1)

		#y_class = K.argmax(y_pred, axis=1)
		#w = tf.gather(WEIGHTS, y_class)
		#return w
		return K.max(y * WEIGHTS, axis=1)


	model = tf.keras.Sequential()
	model.add(tf.keras.layers.Dense(500, activation='relu', input_dim=X_data.shape[1]))
	model.add(tf.keras.layers.Dense(300, activation='relu'))
	model.add(tf.keras.layers.Dense(100, activation='relu'))
	model.add(tf.keras.layers.Dense(len(np.unique(y_data)), activation='softmax'))
	model.compile(optimizer='adam',
				  loss=customLoss,
				  metrics=['accuracy'])


	scaler = MinMaxScaler()
	X_train_scaled = scaler.fit_transform(X_data[train_ids])
	X_test_scaled = scaler.transform(X_data[test_ids])

	model.fit(X_train_scaled, one_hot_labels[train_ids], epochs=2000, batch_size=len(runtimes))
	predictions = model.predict_classes(X_test_scaled)
	print(predictions)

	all_runtimes_in_cv_folds.extend(get_runtime_for_fold_predictions(predictions, test_ids, encoder.categories_[0]))

print('metalearning cv' + " avg runtime: " + str(np.nanmean(all_runtimes_in_cv_folds)) + " median runtime: " + str(np.nanmedian(all_runtimes_in_cv_folds)) + ' std runtime: ' + str(np.nanstd(all_runtimes_in_cv_folds)))

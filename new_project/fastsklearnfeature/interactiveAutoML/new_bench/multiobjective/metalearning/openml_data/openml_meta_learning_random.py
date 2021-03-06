import copy
from sklearn.metrics import make_scorer
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
import pickle
from sklearn.model_selection import StratifiedKFold
import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import time
import numpy as np

from fastsklearnfeature.interactiveAutoML.feature_selection.fcbf_package import variance
from fastsklearnfeature.interactiveAutoML.feature_selection.fcbf_package import model_score
from fastsklearnfeature.interactiveAutoML.feature_selection.fcbf_package import chi2_score_wo
from fastsklearnfeature.interactiveAutoML.feature_selection.fcbf_package import f_anova_wo


from fastsklearnfeature.interactiveAutoML.feature_selection.fcbf_package import fcbf
from fastsklearnfeature.interactiveAutoML.feature_selection.fcbf_package import my_mcfs
from sklearn.model_selection import train_test_split
from fastsklearnfeature.interactiveAutoML.feature_selection.fcbf_package import my_fisher_score
from functools import partial
from hyperopt import fmin, hp, tpe, Trials, STATUS_OK

from sklearn.feature_selection import mutual_info_classif
from fastsklearnfeature.interactiveAutoML.fair_measure import true_positive_rate_score
from fastsklearnfeature.interactiveAutoML.new_bench.multiobjective.robust_measure import robust_score
from skrebate import ReliefF
import fastsklearnfeature.interactiveAutoML.new_bench.multiobjective.metalearning.strategies.multiprocessing_global as mp_global
import diffprivlib.models as models
from sklearn.model_selection import GridSearchCV

from fastsklearnfeature.interactiveAutoML.new_bench.multiobjective.metalearning.strategies.fullfeatures import fullfeatures
from fastsklearnfeature.interactiveAutoML.new_bench.multiobjective.metalearning.strategies.weighted_ranking import weighted_ranking
from fastsklearnfeature.interactiveAutoML.new_bench.multiobjective.metalearning.strategies.hyperparameter_optimization import TPE
from fastsklearnfeature.interactiveAutoML.new_bench.multiobjective.metalearning.strategies.hyperparameter_optimization import simulated_annealing
from fastsklearnfeature.interactiveAutoML.new_bench.multiobjective.metalearning.strategies.evolution import evolution
from fastsklearnfeature.interactiveAutoML.new_bench.multiobjective.metalearning.strategies.exhaustive import exhaustive
from fastsklearnfeature.interactiveAutoML.new_bench.multiobjective.metalearning.strategies.forward_floating_selection import forward_selection
from fastsklearnfeature.interactiveAutoML.new_bench.multiobjective.metalearning.strategies.backward_floating_selection import backward_selection
from fastsklearnfeature.interactiveAutoML.new_bench.multiobjective.metalearning.strategies.forward_floating_selection import forward_floating_selection
from fastsklearnfeature.interactiveAutoML.new_bench.multiobjective.metalearning.strategies.backward_floating_selection import backward_floating_selection
from fastsklearnfeature.interactiveAutoML.new_bench.multiobjective.metalearning.strategies.recursive_feature_elimination import recursive_feature_elimination
from fastsklearnfeature.interactiveAutoML.new_bench.multiobjective.bench_utils import get_fair_data1_validation
from concurrent.futures import TimeoutError
from pebble import ProcessPool, ProcessExpired
import os


def my_function(config_id):
	conf = mp_global.configurations[config_id]
	result = conf['main_strategy'](mp_global.X_train,
								   mp_global.X_validation,
								   mp_global.X_train_val,
								   mp_global.X_test,
								   mp_global.y_train,
								   mp_global.y_validation,
								   mp_global.y_train_val,
								   mp_global.y_test,
								   mp_global.names,
								   mp_global.sensitive_ids,
								   ranking_functions=conf['ranking_functions'],
								   clf=mp_global.clf,
								   min_accuracy=mp_global.min_accuracy,
								   min_fairness=mp_global.min_fairness,
								   min_robustness=mp_global.min_robustness,
								   max_number_features=mp_global.max_number_features,
								   max_search_time=mp_global.max_search_time,
								   log_file='/tmp/experiment' + str(current_run_time_id) + '/run' + str(
									   run_counter) + '/strategy' + str(conf['strategy_id']) + '.pickle')
	result['strategy_id'] = conf['strategy_id']
	return result

current_run_time_id = time.time()

time_limit = 60 * 60 * 3
number_of_runs = 1


cv_splitter = StratifiedKFold(5, random_state=42)

auc_scorer = make_scorer(roc_auc_score, greater_is_better=True, needs_threshold=True)

os.mkdir('/tmp/experiment' + str(current_run_time_id))

run_counter = 0
while True:

	#create folder to store files:
	os.mkdir('/tmp/experiment' + str(current_run_time_id) + '/run' + str(run_counter))

	X_train, X_validation, X_train_val, X_test, y_train, y_validation, y_train_val, y_test, names, sensitive_ids, key, sensitive_attribute_id = get_fair_data1_validation()

	#run on tiny sample
	if X_train.shape[0] > 100:
		X_train_tiny, _, y_train_tiny, _ = train_test_split(X_train, y_train, train_size=100, random_state=42, stratify=y_train)
	else:
		X_train_tiny = X_train
		y_train_tiny = y_train

	fair_train_tiny = make_scorer(true_positive_rate_score, greater_is_better=True, sensitive_data=X_train_tiny[:, sensitive_ids[0]])

	mp_global.X_train = X_train
	mp_global.X_validation = X_validation
	mp_global.X_train_val = X_train_val
	mp_global.X_test = X_test
	mp_global.y_train = y_train
	mp_global.y_validation = y_validation
	mp_global.y_train_val = y_train_val
	mp_global.y_test = y_test
	mp_global.names = names
	mp_global.sensitive_ids = sensitive_ids
	mp_global.cv_splitter = cv_splitter


	def objective(hps):
		print(hps)

		try:
			cv_k = 1.0
			cv_privacy = hps['privacy']
			model = LogisticRegression(class_weight='balanced')
			if type(cv_privacy) == type(None):
				cv_privacy = X_train_tiny.shape[0]
			else:
				model = models.LogisticRegression(epsilon=cv_privacy, class_weight='balanced')

			robust_scorer = make_scorer(robust_score, greater_is_better=True, X=X_train_tiny, y=y_train_tiny, model=model,
										feature_selector=None, scorer=auc_scorer)


			small_start_time = time.time()

			cv = GridSearchCV(model, param_grid={'C': [1.0]}, scoring={'AUC': auc_scorer, 'Fairness': fair_train_tiny, 'Robustness': robust_scorer}, refit=False, cv=cv_splitter)
			cv.fit(X_train_tiny, pd.DataFrame(y_train_tiny))
			cv_acc = cv.cv_results_['mean_test_AUC'][0]
			cv_fair = 1.0 - cv.cv_results_['mean_test_Fairness'][0]
			cv_robust = 1.0 - cv.cv_results_['mean_test_Robustness'][0]

			cv_time = time.time() - small_start_time


			#construct feature vector
			feature_list = []
			#user-specified constraints
			feature_list.append(hps['accuracy'])
			feature_list.append(hps['fairness'])
			feature_list.append(hps['k'])
			feature_list.append(hps['k'] * X_train.shape[1])
			feature_list.append(hps['robustness'])
			feature_list.append(cv_privacy)
			feature_list.append(hps['search_time'])
			#differences to sample performance
			feature_list.append(cv_acc - hps['accuracy'])
			feature_list.append(cv_fair - hps['fairness'])
			feature_list.append(cv_k - hps['k'])
			feature_list.append((cv_k - hps['k']) * X_train.shape[1])
			feature_list.append(cv_robust - hps['robustness'])
			feature_list.append(cv_time)
			#privacy constraint is always satisfied => difference always zero => constant => unnecessary

			#metadata features
			feature_list.append(X_train.shape[0])#number rows
			feature_list.append(X_train.shape[1])#number columns

			features = np.array(feature_list)

			#predict the best model and calculate uncertainty

			loss = 0
			return {'loss': loss, 'status': STATUS_OK, 'features': features, 'search_time': hps['search_time'], 'constraints': hps }
		except:
			return {'loss': np.inf, 'status': STATUS_OK}



	space = {
			 'k': hp.choice('k_choice',
							[
								(1.0),
								(hp.uniform('k_specified', 0, 1))
							]),
			 'accuracy': hp.uniform('accuracy_specified', 0.5, 1),
			 'fairness': hp.choice('fairness_choice',
							[
								(0.0),
								(hp.uniform('fairness_specified', 0, 1))
							]),
			 'privacy': hp.choice('privacy_choice',
							[
								(None),
								(hp.lognormal('privacy_specified', 0, 1))
							]),
			 'robustness': hp.choice('robustness_choice',
							[
								(0.0),
								(hp.uniform('robustness_specified', 0, 1))
							]),
		     'search_time': hp.uniform('search_time_specified', 10, time_limit
									   ), # in seconds
			}

	trials = Trials()
	runs_per_dataset = 0
	i = 1
	while True:
		fmin(objective, space=space, algo=tpe.suggest, max_evals=i, trials=trials, show_progressbar=False)
		i += 1

		if trials.trials[-1]['result']['loss'] == np.inf:
			break

		#break, once convergence tolerance is reached and generate new dataset
		last_trial = trials.trials[-1]
		most_uncertain_f = last_trial['misc']['vals']
		#print(most_uncertain_f)


		min_accuracy = most_uncertain_f['accuracy_specified'][0]
		min_fairness = 0.0
		if most_uncertain_f['fairness_choice'][0]:
			min_fairness = most_uncertain_f['fairness_specified'][0]
		min_robustness = 0.0
		if most_uncertain_f['robustness_choice'][0]:
			min_robustness = most_uncertain_f['robustness_specified'][0]
		max_number_features = 1.0
		if most_uncertain_f['k_choice'][0]:
			max_number_features = most_uncertain_f['k_specified'][0]

		max_search_time = most_uncertain_f['search_time_specified'][0]

		# Execute each search strategy with a given time limit (in parallel)
		# maybe run multiple times to smooth stochasticity

		model = LogisticRegression(class_weight='balanced')
		if most_uncertain_f['privacy_choice'][0]:
			model = models.LogisticRegression(epsilon=most_uncertain_f['privacy_specified'][0], class_weight='balanced')


		mp_global.clf = model
		#define rankings
		rankings = [variance,
					chi2_score_wo,
					fcbf,
					my_fisher_score,
					mutual_info_classif,
					my_mcfs]
		#rankings.append(partial(model_score, estimator=ExtraTreesClassifier(n_estimators=1000))) #accuracy ranking
		#rankings.append(partial(robustness_score, model=model, scorer=auc_scorer)) #robustness ranking
		#rankings.append(partial(fairness_score, estimator=ExtraTreesClassifier(n_estimators=1000), sensitive_ids=sensitive_ids)) #fairness ranking
		rankings.append(partial(model_score, estimator=ReliefF(n_neighbors=10)))  # relieff

		mp_global.min_accuracy = min_accuracy
		mp_global.min_fairness = min_fairness
		mp_global.min_robustness = min_robustness
		mp_global.max_number_features = max_number_features
		mp_global.max_search_time = max_search_time

		mp_global.configurations = []
		#add single rankings
		strategy_id = 1
		for r in range(len(rankings)):
			for run in range(number_of_runs):
				configuration = {}
				configuration['ranking_functions'] = copy.deepcopy([rankings[r]])
				configuration['run_id'] = copy.deepcopy(run)
				configuration['main_strategy'] = copy.deepcopy(weighted_ranking)
				configuration['strategy_id'] = copy.deepcopy(strategy_id)
				mp_global.configurations.append(configuration)
			strategy_id +=1

		main_strategies = [TPE,
						   simulated_annealing,
						   evolution,
						   exhaustive,
						   forward_selection,
						   backward_selection,
						   forward_floating_selection,
						   backward_floating_selection,
						   recursive_feature_elimination,
						   fullfeatures]

		#run main strategies
		for strategy in main_strategies:
			for run in range(number_of_runs):
					configuration = {}
					configuration['ranking_functions'] = []
					configuration['run_id'] = copy.deepcopy(run)
					configuration['main_strategy'] = copy.deepcopy(strategy)
					configuration['strategy_id'] = copy.deepcopy(strategy_id)
					mp_global.configurations.append(configuration)
			strategy_id += 1


		with ProcessPool(max_workers=17) as pool:
			future = pool.map(my_function, range(len(mp_global.configurations)), timeout=max_search_time)

			iterator = future.result()
			while True:
				try:
					result = next(iterator)
				except StopIteration:
					break
				except TimeoutError as error:
					print("function took longer than %d seconds" % error.args[1])
				except ProcessExpired as error:
					print("%s. Exit code: %d" % (error, error.exitcode))
				except Exception as error:
					print("function raised %s" % error)
					#print(error.traceback)  # Python's traceback of remote process


		# pickle everything and store it
		one_big_object = {}
		one_big_object['features'] = trials.trials[-1]['result']['features']
		one_big_object['dataset_id'] = key
		one_big_object['constraint_set_list'] = trials.trials[-1]['result']['constraints']

		with open('/tmp/experiment' + str(current_run_time_id) + '/run' + str(run_counter) + '/run_info.pickle', 'wb') as f_log:
			pickle.dump(one_big_object, f_log)


		run_counter += 1

		trials = Trials()
		i = 1
		runs_per_dataset += 1
		break



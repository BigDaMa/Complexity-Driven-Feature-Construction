import autograd.numpy as anp
import numpy as np
from pymoo.util.misc import stack
from pymoo.model.problem import Problem
import numpy as np
import pickle
from fastsklearnfeature.candidates.CandidateFeature import CandidateFeature
from fastsklearnfeature.candidates.RawFeature import RawFeature
from fastsklearnfeature.transformations.OneHotTransformation import OneHotTransformation
from typing import List, Dict, Set
from fastsklearnfeature.interactiveAutoML.CreditWrapper import run_pipeline
from pymoo.algorithms.so_genetic_algorithm import GA
from pymoo.factory import get_crossover, get_mutation, get_sampling
from pymoo.optimize import minimize
from pymoo.algorithms.nsga2 import NSGA2
import matplotlib.pyplot as plt

which_experiment = 'experiment3'#'experiment1'

numeric_representations: List[CandidateFeature] = pickle.load(open("/home/felix/phd/feature_constraints/" + str(which_experiment) + "/features.p", "rb"))

filtered = numeric_representations

'''
filtered = []
for f in numeric_representations:
	if isinstance(f, RawFeature):
		filtered.append(f)
	else:
		if isinstance(f.transformation, OneHotTransformation):
			filtered.append(f)
numeric_representations = filtered
'''

y_test = pickle.load(open("/home/felix/phd/feature_constraints/" + str(which_experiment) + "/y_test.p", "rb"))

#todo: measure TP for each group and add objective
#todo: try misclassification constraint
#todo: restart search

bit2results= {}



# define an objective function
def objective(features):
	score, test, pred_test, std_score, proba_pred_test = run_pipeline(features, c=1.0, runs=1)
	#print(features)


	complexity = 0
	for f in range(len(numeric_representations)):
		if features[f]:
			#complexity += np.square(numeric_representations[f].get_complexity())
			complexity += numeric_representations[f].get_complexity()

	print('cv: ' + str(score) + ' test: ' + str(test) + ' complexity: ' + str(complexity))

	bit2results[tuple(features)] = [1.0 - score, complexity, std_score, 1.0 - test]

	return 1.0 - score, complexity, std_score

class MyProblem(Problem):

	def __init__(self):
		super().__init__(n_var=len(numeric_representations),
                         n_obj=2,
                         n_constr=0, xl=0, xu=1, type_var=anp.bool)

	def _evaluate(self, x, out, *args, **kwargs):
		f1_all = []
		f2_all = []
		f3_all = []

		for i in range(len(x)):
			f1, f2, f3 = objective(x[i])
			f1_all.append(f1)
			f2_all.append(f2)
			f3_all.append(f3)

		out["F"] = anp.column_stack([f1_all, f2_all])
		#out["G"] = anp.column_stack([g1])



problem = MyProblem()

'''
algorithm = GA(
    pop_size=10,
    sampling=get_sampling("bin_random"),
    crossover=get_crossover("bin_hux"),
    mutation=get_mutation("bin_bitflip"),
    elimate_duplicates=True)
'''
#algorithm = NSGA2(pop_size=10, elimate_duplicates=True)
algorithm = NSGA2(pop_size=5,
				  sampling=get_sampling("bin_random"),
				  crossover=get_crossover("bin_hux"),#get_crossover("bin_two_point"),
				  mutation=get_mutation("bin_bitflip"),
				  elimate_duplicates=True)

res = minimize(problem,
               algorithm,
               ('n_gen', 100),
               disp=False)

print("Best solution found: %s" % res.X.astype(np.int))
print("Function value: %s" % res.F)

print("all:")
for i in range(len(res.X)):
	print(bit2results[tuple(res.X[i])])

acc = []
complexity = []
for element in res.F:
	acc.append(element[0])
	complexity.append(element[1])

complexity = np.array(complexity)
acc = np.array(acc)

ids = np.argsort(complexity)


plt.plot(complexity[ids], acc[ids])
plt.xlabel('Complexity')
plt.ylabel('Loss: 1.0 - AUC')
plt.show()

print('all all: ')
for _,v in bit2results.items():
	print(str(v) +',')

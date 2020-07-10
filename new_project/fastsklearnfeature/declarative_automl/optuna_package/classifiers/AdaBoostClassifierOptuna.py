from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import AdaBoostClassifier
import numpy as np

class AdaBoostClassifierOptuna(AdaBoostClassifier):
    def init_hyperparameters(self, trial, X, y):
        self.name = 'AdaBoostClassifier_'
        self.n_estimators = trial.suggest_int(self.name + "n_estimators", 50, 500, log=False)
        self.learning_rate = trial.suggest_loguniform(self.name + "learning_rate", 0.01, 2)
        self.algorithm = trial.suggest_categorical(self.name + "algorithm", ["SAMME.R", "SAMME"])
        self.max_depth = trial.suggest_int(self.name + "max_depth", 1, 10, log=False)
        self.base_estimator = DecisionTreeClassifier(max_depth=self.max_depth)
        self.classes_ = np.unique(y.astype(int))
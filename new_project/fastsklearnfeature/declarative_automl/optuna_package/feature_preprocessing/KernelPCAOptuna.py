from sklearn.decomposition import KernelPCA

class KernelPCAOptuna(KernelPCA):
    def init_hyperparameters(self, trial, X, y):
        self.name = 'KernelPCA_'

        self.n_components = trial.suggest_int(self.name + "n_components", min([10, X.shape[1]]), X.shape[1], log=False)
        self.kernel = trial.suggest_categorical(self.name + 'kernel', ['poly', 'rbf', 'sigmoid', 'cosine'])
        self.gamma = trial.suggest_loguniform(self.name + "gamma", 3.0517578125e-05, 8)
        self.degree = trial.suggest_int(self.name + 'degree', 2, 5, log=False)
        self.coef0 = trial.suggest_uniform(self.name + "coef0", -1, 1)
        self.remove_zero_eig = True


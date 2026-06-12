from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier


class GradientBoostingCandidate:
    def __init__(self, hyperparameters: dict):
        self.model = GradientBoostingClassifier(
            n_estimators=hyperparameters.get("n_estimators", 100),
            learning_rate=hyperparameters.get("learning_rate", 0.1),
            max_depth=hyperparameters.get("max_depth", 3),
            random_state=hyperparameters.get("random_state", 42),
        )

    def fit(self, X, y):
        self.model.fit(X, y)
        return self

    def predict_proba(self, X):
        return self.model.predict_proba(X)


class RandomForestCandidate:
    def __init__(self, hyperparameters: dict):
        self.model = RandomForestClassifier(
            n_estimators=hyperparameters.get("n_estimators", 100),
            max_depth=hyperparameters.get("max_depth"),
            random_state=hyperparameters.get("random_state", 42),
        )

    def fit(self, X, y):
        self.model.fit(X, y)
        return self

    def predict_proba(self, X):
        return self.model.predict_proba(X)

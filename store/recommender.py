import numpy as np
import random
import statistics


class Recommender:
    def __init__(self, ratings):
        self.ratings = ratings
        self.sim_mat = None
        self._calculate_similarity_matrix()

    @staticmethod
    def _similarity(a, b):
        basis = np.where(a > 0, 1, 0) * np.where(b > 0, 1, 0)
        _a = a * basis
        _b = b * basis
        r = _a.dot(_b) / (np.linalg.norm(_a) * np.linalg.norm(_b))
        return r

    def _calculate_similarity_matrix(self):
        user = self.ratings.shape[0]
        m = np.zeros((user, user))
        for i, a in enumerate(self.ratings):
            for j, b in enumerate(self.ratings):
                m[i, j] = Recommender._similarity(a, b)
        self.sim_mat = m

    def _estimate_ratings(self, user_id):
        weights = self.sim_mat[user_id].reshape((self.sim_mat[user_id].shape[0], 1))
        weighted_ratings = weights * self.ratings
        w = np.zeros((weighted_ratings.shape[1],))
        for i, r in enumerate(weighted_ratings.T):
            w[i] = statistics.mean(filter(lambda x: x != 0, r.tolist()))
        return w.T

    def recommend(self, user_id):
        estimated_ratings = list(enumerate(self._estimate_ratings(user_id)))
        estimated_ratings.sort(key=lambda x: x[1], reverse=True)
        items, _ = zip(*estimated_ratings)
        return items


if __name__ == "__main__":
    # Tests
    np.set_printoptions(precision=3)
    USERS = 100
    ITEMS = 1000

    ratings = np.arange(0, USERS * ITEMS)
    f = np.vectorize(lambda _: random.randint(0, 6))
    ratings = f(ratings).reshape((USERS, ITEMS))

    recommender = Recommender(ratings)
    print(recommender.recommend(2))

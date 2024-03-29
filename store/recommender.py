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
        mag = np.linalg.norm(_a) * np.linalg.norm(_b)
        return _a.dot(_b) / mag if mag != 0 else 0.5

    def _calculate_similarity_matrix(self):
        num_users = self.ratings.shape[0]
        similarity_matrix = np.zeros((num_users, num_users))
        for user_id_a, ratings_by_user_a in enumerate(self.ratings):
            for user_id_b, ratings_by_user_b in enumerate(self.ratings):
                similarity_matrix[user_id_a, user_id_b] = Recommender._similarity(ratings_by_user_a, ratings_by_user_b)
        self.sim_mat = similarity_matrix

    def _estimate_ratings(self, user_id):
        weights = self.sim_mat[user_id].reshape((self.sim_mat[user_id].shape[0], 1))
        weighted_ratings = weights * self.ratings
        w = np.zeros((weighted_ratings.shape[1],))
        for i, r in enumerate(weighted_ratings.T):
            weighted_nums = list(filter(lambda x: x != 0, r.tolist()))
            w[i] = statistics.mean(weighted_nums) if weighted_nums else 0
        return w.T

    def recommend(self, user_id):
        estimated_ratings = list(enumerate(self._estimate_ratings(user_id)))
        estimated_ratings.sort(key=lambda x: x[1], reverse=True)
        items, _ = zip(*estimated_ratings)
        return items


if __name__ == "__main__":
    # Tests
    np.set_printoptions(precision=3)
    USERS = 10
    ITEMS = 10

    ratings = np.arange(0, USERS * ITEMS)
    f = np.vectorize(lambda _: random.randint(1, 5) if random.randint(0, 9) < 5 else 0)
    ratings = f(ratings).reshape((USERS, ITEMS))
    print(ratings)

    recommender = Recommender(ratings)
    print(recommender.recommend(2))

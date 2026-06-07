import numpy as np
from sklearn.cluster import KMeans

# Les 48 racines triées (ordre croissant) – à copier de sqrt_lambda
roots = np.array([
    0.066136959, 0.104861556, 0.105819546, 0.135301931,
    0.171977681, 0.193286510, 0.217318285, 0.251706536,
    0.281751380, 0.308944245, 0.342536900, 0.360145691,
    0.389044757, 0.426899914, 0.539423867, 0.555869353,
    0.611492405, 0.628435246, 0.726794491, 0.783638283,
    0.868248673, 0.894790972, 0.895000741, 1.181361718,
    1.388242400, 1.459652785, 1.504114125, 1.582953046,
    1.725183114, 1.831271203, 1.841477693, 1.891359664,
    2.017424480, 2.092834951, 2.304598960, 2.524926754,
    2.911315620, 3.157658906, 3.158280845, 3.279177783,
    3.289042432, 3.851497776, 4.571886169, 4.724739150,
    4.755055358, 5.943089000, 7.408061012, 8.102307717
])

# Taille des classes de la double couverture octaédrique
# (une représentation de dimension 4 donnerait 4 valeurs par classe,
# mais ici on force 7 classes pour voir)
kmeans = KMeans(n_clusters=7, random_state=0, n_init='auto')
labels = kmeans.fit_predict(roots.reshape(-1, 1))

print("Classification automatique (KMeans, 7 clusters) :")
for cluster in range(7):
    indices = np.where(labels == cluster)[0]
    values = roots[indices]
    print(f"Classe {cluster}: {len(values)} éléments -> valeurs de {values[0]:.3f} à {values[-1]:.3f}")
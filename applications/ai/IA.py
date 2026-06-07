#!/usr/bin/env python3
# neurone_analysis.py

import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from itertools import combinations, product

# ============================================================
# 1. Les 15 β (fixes)
# ============================================================
beta = np.array([
    0.066136959, 0.281751380, 0.555869353, 0.868248673,
    1.504114125, 1.725183114, 1.831271203, 2.017424480,
    2.092834951, 2.524926754, 3.279177783, 3.851497776,
    4.571886169, 4.724739150, 7.408061012
])

# ============================================================
# 2. Génération des combinaisons ternaires (ε)
# ============================================================
def generate_ternary_combinations(max_active=6):
    n = len(beta)
    combos = []
    for k in range(1, max_active+1):
        for idx in combinations(range(n), k):
            for signs in product([-1, 1], repeat=k):
                coeff = np.zeros(n)
                for i, s in zip(idx, signs):
                    coeff[i] = s
                # normalisation : premier coefficient non nul >0
                first = next(i for i in range(n) if coeff[i] != 0)
                if coeff[first] < 0:
                    coeff = -coeff
                combos.append(coeff)
    # Enlever les doublons
    combos = np.array(list({tuple(c) for c in combos}))
    return combos

print("Génération des combinaisons ternaires d'initialisation...")
ternary_combos = generate_ternary_combinations(max_active=6)
print(f"Nombre de combinaisons ε disponibles : {len(ternary_combos)}")

# ============================================================
# 3. Réseau ternaire avec poids en float (pour l'entraînement)
#    mais contraints à rester dans [-1,0,1] après chaque mise à jour
# ============================================================
class TernaryNeuralNetwork:
    def __init__(self, input_dim, hidden_units, output_dim, learning_rate=0.01):
        self.input_dim = input_dim
        self.hidden_units = hidden_units
        self.output_dim = output_dim
        self.lr = learning_rate
        
        # Initialisation ternaire des poids (valeurs float, mais -1,0,1)
        self.W1 = self._random_ternary_matrix(hidden_units, input_dim).astype(float)
        self.W2 = self._random_ternary_matrix(output_dim, hidden_units).astype(float)
        self.b1 = np.zeros(hidden_units)
        self.b2 = np.zeros(output_dim)
    
    def _random_ternary_matrix(self, rows, cols):
        # Retourne une matrice avec des -1,0,1
        return np.random.choice([-1,0,1], size=(rows, cols), p=[1/3,1/3,1/3])
    
    def _clip_to_ternary(self, W):
        # Arrondir à -1,0,1 et remettre en float
        return np.clip(np.round(W, 0), -1, 1).astype(float)
    
    def forward(self, X):
        self.z1 = X @ self.W1.T + self.b1
        self.a1 = np.tanh(self.z1)
        self.z2 = self.a1 @ self.W2.T + self.b2
        self.a2 = 1 / (1 + np.exp(-self.z2))
        return self.a2
    
    def backward(self, X, y_true, y_pred):
        m = X.shape[0]
        # Gradient pour la sortie
        dloss_dz2 = y_pred - y_true.reshape(-1,1)
        dW2 = (dloss_dz2.T @ self.a1) / m
        db2 = np.mean(dloss_dz2, axis=0)
        # Gradient pour la couche cachée
        dloss_da1 = dloss_dz2 @ self.W2
        dloss_dz1 = dloss_da1 * (1 - self.a1**2)
        dW1 = (dloss_dz1.T @ X) / m
        db1 = np.mean(dloss_dz1, axis=0)
        # Mise à jour (en float)
        self.W1 -= self.lr * dW1
        self.W2 -= self.lr * dW2
        self.b1 -= self.lr * db1
        self.b2 -= self.lr * db2
        # Projection ternaire après chaque pas
        self.W1 = self._clip_to_ternary(self.W1)
        self.W2 = self._clip_to_ternary(self.W2)
    
    def train(self, X, y, epochs, batch_size=32, verbose=True):
        n = X.shape[0]
        losses = []
        for epoch in range(epochs):
            indices = np.random.permutation(n)
            epoch_loss = 0
            for i in range(0, n, batch_size):
                batch_idx = indices[i:i+batch_size]
                X_batch = X[batch_idx]
                y_batch = y[batch_idx]
                y_pred = self.forward(X_batch)
                # Binary cross-entropy
                loss = -np.mean(y_batch * np.log(y_pred+1e-8) + (1-y_batch) * np.log(1-y_pred+1e-8))
                epoch_loss += loss
                self.backward(X_batch, y_batch, y_pred)
            losses.append(epoch_loss / (n // batch_size + 1))
            if verbose and epoch % 100 == 0:
                print(f"Epoch {epoch}, loss = {losses[-1]:.6f}")
        return losses

# ============================================================
# 4. Jeu de données synthétique
# ============================================================
X, y = make_classification(n_samples=2000, n_features=15, n_informative=10,
                           n_redundant=5, n_clusters_per_class=1,
                           random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# ============================================================
# 5. Entraînement du réseau ternaire avec initialisation aléatoire
# ============================================================
print("\n=== Réseau ternaire avec initialisation aléatoire ===")
nn_random = TernaryNeuralNetwork(input_dim=15, hidden_units=32, output_dim=1, learning_rate=0.05)
losses_random = nn_random.train(X_train, y_train, epochs=500, batch_size=64)
y_pred_random = (nn_random.forward(X_test) > 0.5).astype(int).flatten()
acc_random = np.mean(y_pred_random == y_test)

# ============================================================
# 6. Entraînement avec initialisation basée sur les combinaisons ε
# ============================================================
print("\n=== Réseau ternaire avec initialisation par combinaisons ε ===")
nn_eps = TernaryNeuralNetwork(input_dim=15, hidden_units=32, output_dim=1, learning_rate=0.05)
# On remplace les poids de la première couche par des combinaisons ε aléatoires
# (choisies parmi les 221173 combinaisons générées)
idx = np.random.choice(len(ternary_combos), size=(nn_eps.W1.shape[0],), replace=True)
for i, j in enumerate(idx):
    nn_eps.W1[i] = ternary_combos[j].astype(float)
# On garde la deuxième couche aléatoire
losses_eps = nn_eps.train(X_train, y_train, epochs=500, batch_size=64)
y_pred_eps = (nn_eps.forward(X_test) > 0.5).astype(int).flatten()
acc_eps = np.mean(y_pred_eps == y_test)

# ============================================================
# 7. Tracé des courbes de perte
# ============================================================
plt.figure(figsize=(10,6))
plt.plot(losses_random, label='Init aléatoire')
plt.plot(losses_eps, label='Init ε')
plt.xlabel('Époque')
plt.ylabel('Perte')
plt.title('Comparaison de l\'initialisation ternaire')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('ternary_nn_training.png')
print("Graphique sauvegardé : ternary_nn_training.png")
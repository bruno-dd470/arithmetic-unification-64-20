#!/usr/bin/env python3
# ternary_nn_multirun_plots.py

import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from itertools import combinations, product
import time

# ============================================================
# 1. Les 15 β (constants)
# ============================================================
beta = np.array([
    0.066136959, 0.281751380, 0.555869353, 0.868248673,
    1.504114125, 1.725183114, 1.831271203, 2.017424480,
    2.092834951, 2.524926754, 3.279177783, 3.851497776,
    4.571886169, 4.724739150, 7.408061012
])

# ============================================================
# 2. Génération des combinaisons ε
# ============================================================
def generate_epsilon_combinations(max_active=6):
    n = len(beta)
    combos = []
    for k in range(1, max_active+1):
        for idx in combinations(range(n), k):
            for signs in product([-1, 1], repeat=k):
                coeff = np.zeros(n)
                for i, s in zip(idx, signs):
                    coeff[i] = s
                first = next(i for i in range(n) if coeff[i] != 0)
                if coeff[first] < 0:
                    coeff = -coeff
                combos.append(coeff)
    combos = np.array(list({tuple(c) for c in combos}))
    return combos

print("Génération des combinaisons ε...")
epsilon_combos = generate_epsilon_combinations()
print(f"Nombre de combinaisons ε : {len(epsilon_combos)}")

# ============================================================
# 3. Réseau ternaire
# ============================================================
class TernaryNN:
    def __init__(self, input_dim, hidden_units, output_dim, lr=0.05, init='random'):
        self.lr = lr
        self.input_dim = input_dim
        self.hidden_units = hidden_units
        self.output_dim = output_dim
        
        if init == 'random':
            self.W1 = np.random.choice([-1,0,1], size=(hidden_units, input_dim)).astype(float)
            self.W2 = np.random.choice([-1,0,1], size=(output_dim, hidden_units)).astype(float)
        else:
            self.W1 = np.zeros((hidden_units, input_dim), dtype=float)
            for i in range(hidden_units):
                idx = np.random.randint(len(epsilon_combos))
                self.W1[i] = epsilon_combos[idx]
            self.W2 = np.random.choice([-1,0,1], size=(output_dim, hidden_units)).astype(float)
        
        self.b1 = np.zeros(hidden_units)
        self.b2 = np.zeros(output_dim)
    
    def _clip_ternary(self, W):
        return np.clip(np.round(W, 0), -1, 1).astype(float)
    
    def forward(self, X):
        self.z1 = X @ self.W1.T + self.b1
        self.a1 = np.tanh(self.z1)
        self.z2 = self.a1 @ self.W2.T + self.b2
        self.a2 = 1 / (1 + np.exp(-self.z2))
        return self.a2
    
    def backward(self, X, y_true, y_pred):
        m = X.shape[0]
        dloss_dz2 = y_pred - y_true.reshape(-1,1)
        dW2 = (dloss_dz2.T @ self.a1) / m
        db2 = np.mean(dloss_dz2, axis=0)
        dloss_da1 = dloss_dz2 @ self.W2
        dloss_dz1 = dloss_da1 * (1 - self.a1**2)
        dW1 = (dloss_dz1.T @ X) / m
        db1 = np.mean(dloss_dz1, axis=0)
        self.W1 -= self.lr * dW1
        self.W2 -= self.lr * dW2
        self.b1 -= self.lr * db1
        self.b2 -= self.lr * db2
        self.W1 = self._clip_ternary(self.W1)
        self.W2 = self._clip_ternary(self.W2)
    
    def train(self, X, y, epochs, batch_size=64, verbose=False):
        n = X.shape[0]
        history = {'loss': [], 'acc': []}
        for epoch in range(epochs):
            indices = np.random.permutation(n)
            epoch_loss = 0
            epoch_acc = 0
            for i in range(0, n, batch_size):
                batch_idx = indices[i:i+batch_size]
                Xb, yb = X[batch_idx], y[batch_idx]
                pred = self.forward(Xb)
                loss = -np.mean(yb * np.log(pred+1e-8) + (1-yb) * np.log(1-pred+1e-8))
                epoch_loss += loss
                acc = np.mean((pred > 0.5).flatten() == yb)
                epoch_acc += acc
                self.backward(Xb, yb, pred)
            history['loss'].append(epoch_loss / (n // batch_size + 1))
            history['acc'].append(epoch_acc / (n // batch_size + 1))
            if verbose and epoch % 100 == 0:
                print(f"Epoch {epoch}: loss={history['loss'][-1]:.4f}, acc={history['acc'][-1]:.4f}")
        return history

# ============================================================
# 4. Exécution d'un run pour une graine donnée
# ============================================================
def run_single(init_type, seed, n_epochs=500):
    np.random.seed(seed)
    X, y = make_classification(n_samples=2000, n_features=15, n_informative=10,
                               n_redundant=5, n_clusters_per_class=1, random_state=seed)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=seed)
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)
    
    nn = TernaryNN(input_dim=15, hidden_units=32, output_dim=1, init=init_type, lr=0.05)
    hist = nn.train(X_train, y_train, epochs=n_epochs, batch_size=64, verbose=False)
    return hist['loss'], hist['acc']

# ============================================================
# 5. Multi‑runs
# ============================================================
n_runs = 10
n_epochs = 500

all_loss_random = []
all_acc_random = []
all_loss_eps = []
all_acc_eps = []

print("\nExécution des 10 runs pour initialisation aléatoire...")
for seed in range(n_runs):
    print(f"  Run {seed+1}/{n_runs}", end='', flush=True)
    loss, acc = run_single('random', seed, n_epochs)
    all_loss_random.append(loss)
    all_acc_random.append(acc)
    print(" -> terminé")

print("\nExécution des 10 runs pour initialisation ε...")
for seed in range(n_runs):
    print(f"  Run {seed+1}/{n_runs}", end='', flush=True)
    loss, acc = run_single('epsilon', seed, n_epochs)
    all_loss_eps.append(loss)
    all_acc_eps.append(acc)
    print(" -> terminé")

# ============================================================
# 6. Calcul des moyennes et écarts‑types par époque
# ============================================================
arr_loss_random = np.array(all_loss_random)   # shape (n_runs, n_epochs)
arr_acc_random = np.array(all_acc_random)
arr_loss_eps = np.array(all_loss_eps)
arr_acc_eps = np.array(all_acc_eps)

mean_loss_random = np.mean(arr_loss_random, axis=0)
std_loss_random = np.std(arr_loss_random, axis=0)
mean_acc_random = np.mean(arr_acc_random, axis=0) * 100
std_acc_random = np.std(arr_acc_random, axis=0) * 100

mean_loss_eps = np.mean(arr_loss_eps, axis=0)
std_loss_eps = np.std(arr_loss_eps, axis=0)
mean_acc_eps = np.mean(arr_acc_eps, axis=0) * 100
std_acc_eps = np.std(arr_acc_eps, axis=0) * 100

# ============================================================
# 7. Graphiques
# ============================================================
epochs = np.arange(1, n_epochs+1)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Accuracy vs époque
ax1.plot(epochs, mean_acc_random, label='Aléatoire', color='blue', linewidth=1.5)
ax1.fill_between(epochs, mean_acc_random - std_acc_random, mean_acc_random + std_acc_random,
                 alpha=0.2, color='blue')
ax1.plot(epochs, mean_acc_eps, label='Initialisation ε', color='orange', linewidth=1.5)
ax1.fill_between(epochs, mean_acc_eps - std_acc_eps, mean_acc_eps + std_acc_eps,
                 alpha=0.2, color='orange')
ax1.set_xlabel('Époque')
ax1.set_ylabel('Accuracy (%)')
ax1.set_title('Évolution de l\'accuracy')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Loss vs époque
ax2.plot(epochs, mean_loss_random, label='Aléatoire', color='blue', linewidth=1.5)
ax2.fill_between(epochs, mean_loss_random - std_loss_random, mean_loss_random + std_loss_random,
                 alpha=0.2, color='blue')
ax2.plot(epochs, mean_loss_eps, label='Initialisation ε', color='orange', linewidth=1.5)
ax2.fill_between(epochs, mean_loss_eps - std_loss_eps, mean_loss_eps + std_loss_eps,
                 alpha=0.2, color='orange')
ax2.set_xlabel('Époque')
ax2.set_ylabel('Loss (cross‑entropy)')
ax2.set_title('Évolution de la loss')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('accuracy_loss_vs_epoch_multirun.png', dpi=150)
plt.show()

# ============================================================
# 8. Résumé statistique
# ============================================================
print("\n" + "="*50)
print("RÉSUMÉ FINAL (moyenne sur 10 runs)")
print("="*50)
print(f"Aléatoire : accuracy = {mean_acc_random[-1]:.1f}% ± {std_acc_random[-1]:.1f}%")
print(f"ε         : accuracy = {mean_acc_eps[-1]:.1f}% ± {std_acc_eps[-1]:.1f}%")
print(f"Loss finale aléatoire : {mean_loss_random[-1]:.4f} ± {std_loss_random[-1]:.4f}")
print(f"Loss finale ε         : {mean_loss_eps[-1]:.4f} ± {std_loss_eps[-1]:.4f}")
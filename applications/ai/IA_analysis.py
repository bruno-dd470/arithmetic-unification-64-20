#!/usr/bin/env python3
# IA_analysis_corrected.py

import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models, datasets
from itertools import combinations, product
import matplotlib.pyplot as plt

# ============================================================
# 1. Les 15 β (universels)
# ============================================================
beta = np.array([
    0.066136959, 0.281751380, 0.555869353, 0.868248673,
    1.504114125, 1.725183114, 1.831271203, 2.017424480,
    2.092834951, 2.524926754, 3.279177783, 3.851497776,
    4.571886169, 4.724739150, 7.408061012
])

# ============================================================
# 2. Génération des combinaisons ε (ternaires) pour initialiser
#    les poids des couches denses (après projection sur β)
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
epsilon_combos = generate_epsilon_combinations(max_active=6)
print(f"Nombre de combinaisons ε : {len(epsilon_combos)}")

# ============================================================
# 3. Couche de projection fixe sur les β
# ============================================================
class BetaProjection(layers.Layer):
    def __init__(self, beta, **kwargs):
        super().__init__(**kwargs)
        self.beta = tf.constant(beta, dtype=tf.float32)
    
    def call(self, inputs):
        # inputs shape: (batch, input_dim)
        # On veut calculer les 15 produits scalaires entre chaque pixel (poids=β)
        # On fait une multiplication matricielle simple : inputs @ beta.T
        return tf.matmul(inputs, tf.reshape(self.beta, (1, -1)))  # shape (batch, 15)
    
    def get_config(self):
        config = super().get_config()
        config.update({'beta': self.beta.numpy().tolist()})
        return config

# ============================================================
# 4. Construction du réseau avec initialisation ternaire
#    des couches denses (après la projection)
# ============================================================
def get_ternary_initializer(use_epsilon=False):
    """Retourne un initialiseur ternaire pour un layer Dense."""
    if use_epsilon:
        def init(shape, dtype=None):
            # shape = (units, 15) pour la première couche ? Non : (input_dim, units)
            # Ici, après projection, l'entrée a 15 features.
            # On veut que chaque neurone soit initialisé avec une combinaison ε
            input_dim, units = shape
            W = np.zeros(shape, dtype=np.float32)
            for unit in range(units):
                idx = np.random.randint(len(epsilon_combos))
                # ε est de taille 15, on le répète sur les input_dim (qui vaut 15)
                # Les poids pour un neurone sont ε, donc input_dim doit être 15.
                if input_dim != 15:
                    raise ValueError(f"input_dim={input_dim} doit être 15 pour utiliser ε")
                W[:, unit] = epsilon_combos[idx]
            return tf.constant(W, dtype=dtype)
        return init
    else:
        # Initialisation aléatoire ternaire (-1,0,1)
        def init(shape, dtype=None):
            return tf.constant(np.random.choice([-1,0,1], size=shape, p=[1/3,1/3,1/3]).astype(np.float32), dtype=dtype)
        return init

# ============================================================
# 5. Préparation des données
# ============================================================
def load_mnist():
    (x_train, y_train), (x_test, y_test) = datasets.mnist.load_data()
    x_train = x_train.reshape(-1, 28*28).astype('float32') / 255.0
    x_test = x_test.reshape(-1, 28*28).astype('float32') / 255.0
    y_train = tf.keras.utils.to_categorical(y_train, 10)
    y_test = tf.keras.utils.to_categorical(y_test, 10)
    return x_train, y_train, x_test, y_test

def load_cifar10():
    (x_train, y_train), (x_test, y_test) = datasets.cifar10.load_data()
    x_train = x_train.astype('float32') / 255.0
    x_test = x_test.astype('float32') / 255.0
    x_train = x_train.reshape(-1, 32*32*3)
    x_test = x_test.reshape(-1, 32*32*3)
    y_train = tf.keras.utils.to_categorical(y_train.flatten(), 10)
    y_test = tf.keras.utils.to_categorical(y_test.flatten(), 10)
    return x_train, y_train, x_test, y_test

# ============================================================
# 6. Entraînement et évaluation
# ============================================================
def train_and_evaluate(x_train, y_train, x_test, y_test, init_type='random', epochs=10):
    model = models.Sequential()
    # Couche de projection fixe sur β (non entraînée)
    model.add(BetaProjection(beta, trainable=False))
    # Couches denses (poids ternaires)
    model.add(layers.Dense(256, activation='relu',
                           kernel_initializer=get_ternary_initializer(use_epsilon=(init_type=='epsilon'))))
    model.add(layers.Dense(128, activation='relu',
                           kernel_initializer=get_ternary_initializer(use_epsilon=False)))
    model.add(layers.Dense(10, activation='softmax',
                           kernel_initializer=get_ternary_initializer(use_epsilon=False)))
    model.compile(optimizer='adam',
                  loss='categorical_crossentropy',
                  metrics=['accuracy'])
    history = model.fit(x_train, y_train, batch_size=128, epochs=epochs,
                        validation_data=(x_test, y_test), verbose=1)
    acc = history.history['val_accuracy'][-1]
    return acc, history

# ============================================================
# 7. Exécution des tests
# ============================================================
print("\n=== Test sur MNIST ===")
x_train, y_train, x_test, y_test = load_mnist()
acc_random_mnist, hist_random_mnist = train_and_evaluate(x_train, y_train, x_test, y_test, init_type='random', epochs=5)
acc_eps_mnist, hist_eps_mnist = train_and_evaluate(x_train, y_train, x_test, y_test, init_type='epsilon', epochs=5)
print(f"MNIST - Aléatoire : {acc_random_mnist:.4f}, ε : {acc_eps_mnist:.4f}")

print("\n=== Test sur CIFAR-10 ===")
x_train, y_train, x_test, y_test = load_cifar10()
acc_random_cifar, hist_random_cifar = train_and_evaluate(x_train, y_train, x_test, y_test, init_type='random', epochs=10)
acc_eps_cifar, hist_eps_cifar = train_and_evaluate(x_train, y_train, x_test, y_test, init_type='epsilon', epochs=10)
print(f"CIFAR-10 - Aléatoire : {acc_random_cifar:.4f}, ε : {acc_eps_cifar:.4f}")

# ============================================================
# 8. Courbes d'apprentissage
# ============================================================
plt.figure(figsize=(12,5))
plt.subplot(1,2,1)
plt.plot(hist_random_mnist.history['val_accuracy'], label='Aléatoire')
plt.plot(hist_eps_mnist.history['val_accuracy'], label='ε')
plt.title('MNIST - Accuracy validation')
plt.xlabel('Époque')
plt.ylabel('Accuracy')
plt.legend()
plt.grid(True)

plt.subplot(1,2,2)
plt.plot(hist_random_cifar.history['val_accuracy'], label='Aléatoire')
plt.plot(hist_eps_cifar.history['val_accuracy'], label='ε')
plt.title('CIFAR-10 - Accuracy validation')
plt.xlabel('Époque')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.savefig('init_epsilon_comparison.png')
print("Graphique sauvegardé : init_epsilon_comparison.png")
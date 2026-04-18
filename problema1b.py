import numpy as np
import matplotlib.pyplot as plt

# Parámetros físicos
a = 4.0  # Angstroms (Asumido, ajustar si el problema requiere otro)
V = 100.0  # meV
hbar2_2m0 = 3809.98  # Constante hbar^2 / 2m_0 en meV * Angstrom^2

# Módulo G
G_mod = 4 * np.pi / (a * np.sqrt(3))

# Vectores base recíprocos
G1 = G_mod * np.array([np.sqrt(3)/2, -0.5])
G2 = G_mod * np.array([0, 1])

# Puntos de alta simetría
Gamma = np.array([0, 0])
K_point = (4 * np.pi / (3 * a)) * np.array([1, 0])
M_point = (2 * np.pi / (a * np.sqrt(3))) * np.array([np.sqrt(3)/2, 0.5])

# Creación del camino k (250 puntos proporcionales a la distancia)
dist_GK = np.linalg.norm(K_point - Gamma)
dist_KM = np.linalg.norm(M_point - K_point)
dist_MG = np.linalg.norm(Gamma - M_point)
total_dist = dist_GK + dist_KM + dist_MG

n_GK = int(250 * (dist_GK / total_dist))
n_KM = int(250 * (dist_KM / total_dist))
n_MG = 250 - n_GK - n_KM  # Para asegurar exactamente 250 puntos

k_GK = np.linspace(Gamma, K_point, n_GK, endpoint=False)
k_KM = np.linspace(K_point, M_point, n_KM, endpoint=False)
k_MG = np.linspace(M_point, Gamma, n_MG)

k_path = np.vstack((k_GK, k_KM, k_MG))

# Vector de distancias acumuladas para el eje X de la gráfica
k_dist = np.zeros(250)
for i in range(1, 250):
    k_dist[i] = k_dist[i-1] + np.linalg.norm(k_path[i] - k_path[i-1])

# Puntos clave para las etiquetas del eje X
tick_pos = [0, k_dist[n_GK-1], k_dist[n_GK+n_KM-1], k_dist[-1]]
tick_labels = ['$\Gamma$', '$K$', '$M$', '$\Gamma$']

# Base de ondas planas (n1, n2) truncada de -N a N
N_max = 4 # Base de (2*4 + 1)^2 = 81 estados (Suficiente para las primeras bandas)
n_vals = np.arange(-N_max, N_max + 1)
base = [(n1, n2) for n1 in n_vals for n2 in n_vals]
dim = len(base)

# Construcción de la matriz de potencial U (independiente de k)
U = np.zeros((dim, dim))
for i, (n1_i, n2_i) in enumerate(base):
    for j, (n1_j, n2_j) in enumerate(base):
        dn1 = n1_i - n1_j
        dn2 = n2_i - n2_j
        
        # Condiciones de acoplamiento por G1, G2 y G3
        if (dn1, dn2) in [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1)]:
            U[i, j] = V / 2.0

# Cálculo de las bandas de energía
bandas = np.zeros((250, dim))

for idx, k in enumerate(k_path):
    H = np.zeros((dim, dim))
    for i, (n1, n2) in enumerate(base):
        # Vector G correspondiente a este estado de la base
        G_vec = n1 * G1 + n2 * G2
        # Energía cinética
        H[i, i] = hbar2_2m0 * np.linalg.norm(k - G_vec)**2
        
    H_total = H + U
    # Diagonalización
    eigenvalores = np.linalg.eigvalsh(H_total)
    bandas[idx, :] = eigenvalores

# Graficar las primeras 6 bandas
plt.figure(figsize=(8, 6))
for b in range(6):
    plt.plot(k_dist, bandas[:, b], color='b', lw=1.5)

# Formato de la gráfica
for pos in tick_pos:
    plt.axvline(x=pos, color='k', linestyle='--', alpha=0.5)

plt.xticks(tick_pos, tick_labels, fontsize=14)
plt.ylabel('Energía (meV)', fontsize=12)
plt.title('Estructura de Bandas 2D (Red Hexagonal)', fontsize=14)
plt.xlim(0, k_dist[-1])
plt.grid(True, linestyle=':', alpha=0.6)
plt.tight_layout()
plt.show()
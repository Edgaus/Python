import numpy as np
import matplotlib.pyplot as plt

# Constantes físicas
# hbar^2 / 2m_0 en unidades de meV * Angstrom^2
hbar2_2m0 = 3809.98 

def calcular_bandas(a, V, V_prime, N_max=20, num_k=100):
    g = 2 * np.pi / a
    # Zona de Brillouin k en [-g/2, g/2)
    k_vals = np.linspace(-g/2, g/2, num_k, endpoint=False)
    
    # Índices para la base plana
    n_vals = np.arange(-N_max, N_max + 1)
    dim = len(n_vals)
    
    # Matriz para almacenar las energías de las bandas
    bandas = np.zeros((num_k, dim))
    
    # Construcción de la matriz del potencial U (independiente de k)
    U = np.zeros((dim, dim))
    for i in range(dim):
        for j in range(dim):
            diff = abs(i - j)
            if diff == 1:
                U[i, j] = V / 2.0
            elif diff == 2:
                U[i, j] = V_prime / 2.0

    # Diagonalización para cada valor de k
    for ik, k in enumerate(k_vals):
        H = np.zeros((dim, dim))
        
        # Término cinético en la diagonal
        for i, n in enumerate(n_vals):
            H[i, i] = hbar2_2m0 * (k - n * g)**2
            
        # Sumamos el potencial
        H_total = H + U
        
        # Obtenemos los eigenvalores (usamos eigh por ser matriz Hermítica/simétrica)
        eigenvalores = np.linalg.eigvalsh(H_total)
        bandas[ik, :] = eigenvalores

    # Retornamos los k y las primeras 5 bandas
    return k_vals, bandas[:, :5]

# Parámetros de los incisos
casos = [
    {"a": 4, "V": 50, "V_prime": 0, "titulo": "1a.1: a=4 $\\AA$, V=50 meV, V'=0"},
    {"a": 4, "V": 50, "V_prime": 10, "titulo": "1a.2: a=4 $\\AA$, V=50 meV, V'=10 meV"},
    {"a": 20, "V": 50, "V_prime": 0, "titulo": "1a.3: a=20 $\\AA$, V=50 meV, V'=0"}
]

# CAMBIO 1: Configuración del gráfico en formato vertical (3 filas, 1 columna)
# Ajustamos el figsize para que las gráficas no se aplasten
fig, axes = plt.subplots(3, 1, figsize=(8, 15))

for idx, caso in enumerate(casos):
    g = 2 * np.pi / caso["a"]
    k, bandas_5 = calcular_bandas(caso["a"], caso["V"], caso["V_prime"])
    
    # Eje X en unidades de pi/a
    k_norm = k / (np.pi / caso["a"]) 
    
    # En subplots de 1D, axes es un arreglo simple, no necesitamos índices 2D
    ax = axes[idx]
    for b in range(5):
        ax.plot(k_norm, bandas_5[:, b], linewidth=2, label=f'Banda {b+1}')
        
    ax.set_title(caso["titulo"])
    ax.set_xlabel('$k \\ (\\pi/a)$')
    ax.set_ylabel('Energía (meV)')
    ax.set_xlim([-1, 1])
    
    # CAMBIO 2: Escala logarítmica en el eje Y
    ax.set_yscale('log')
    
    # Mejoramos la cuadrícula para que las líneas menores del logaritmo sean visibles
    ax.grid(True, which="both", linestyle='--', alpha=0.7)

# Colocamos la leyenda en la primera gráfica, ajustada para que no estorbe los datos
axes[0].legend(loc='lower right')

plt.tight_layout()
plt.show()
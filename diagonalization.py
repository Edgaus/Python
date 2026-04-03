import numpy as np
import matplotlib.pyplot as plt

def calcular_H_numerica(a, b, params):
    """Construye la matriz Hamiltoniana 3x3 para valores dados de alfa (a) y beta (b)."""
    e1, e2, e3 = params['e1'], params['e2'], params['e3']
    t0, t11, t22, t12 = params['t0'], params['t11'], params['t22'], params['t12']
    
    H = np.zeros((3, 3), dtype=complex)
    
    # Elementos de la diagonal
    H[0, 0] = e1 + 2*t0*(np.cos(2*a) + 2*np.cos(a)*np.cos(b))
    H[1, 1] = e2 + 2*t11*np.cos(2*a) + (t11 + 3*t22)*np.cos(a)*np.cos(b)
    H[2, 2] = e3 + 2*t22*np.cos(2*a) + (3*t11 + t22)*np.cos(a)*np.cos(b)
    
    # Elementos fuera de la diagonal (H12 y su conjugado)
    H[0, 1] = 4j*t12*np.sin(a)*(np.cos(a) - np.cos(b)) - np.sqrt(3)*np.sin(a)*np.sin(b)*(t11 - t22)
    H[1, 0] = np.conj(H[0, 1])
    
    # Elementos fuera de la diagonal (H13 y su conjugado)
    H[0, 2] = -4*t12*np.sin(a)*np.sin(b) + 1j*np.sqrt(3)*np.cos(a)*np.sin(b)*(t11 - t22)
    H[2, 0] = np.conj(H[0, 2])
    
    # Elementos fuera de la diagonal (H23 y su conjugado)
    H[1, 2] = np.sqrt(3)*np.sin(a)*np.sin(b)*(t11 - t22) - 1j*4*t12*np.cos(a)*np.sin(b)
    H[2, 1] = np.conj(H[1, 2])
    
    return H

def plot_estructura_bandas():
    # 1. Parámetros físicos (Según tus notas)
    parametros = {
        'e1': 0.0, 'e2': 1.0, 'e3': 1.0,  # Energías de sitio (e11, e22, e33)
        't0': -1.2,                       # Salto t_0
        't11': -0.52, 't22': 1.05,        # Saltos t_11 y t_22
        't12': 0.5                        # Salto t_12
    }
    
    # 2. Definir los tramos del camino en el espacio k
    N = 100 # Número de puntos por tramo
    
    # Tramo 1: Gamma -> M
    alpha_GM = np.zeros(N)
    beta_GM = np.linspace(0, np.pi, N)
    
    # Tramo 2: M -> K
    alpha_MK = np.linspace(0, np.pi/3, N)
    beta_MK = np.full(N, np.pi)
    
    # Tramo 3: K -> Gamma
    alpha_KG = np.linspace(np.pi/3, 0, N)
    beta_KG = np.linspace(np.pi, 0, N)
    
    # Concatenar todos los tramos en un solo arreglo continuo
    alpha_vals = np.concatenate([alpha_GM, alpha_MK, alpha_KG])
    beta_vals = np.concatenate([beta_GM, beta_MK, beta_KG])
    
    # 3. Calcular eigenvalores a lo largo del camino
    bandas = []
    for a, b in zip(alpha_vals, beta_vals):
        H_num = calcular_H_numerica(a, b, parametros)
        eigenvalores = np.linalg.eigvalsh(H_num) # Diagonalización Hermítica
        bandas.append(eigenvalores)
        
    bandas = np.array(bandas)
    
    # Eje X para la gráfica (índices continuos)
    x_vals = np.arange(len(alpha_vals))
    # Posiciones donde ocurren los puntos de alta simetría
    puntos_simetria = [0, N-1, 2*N-1, 3*N-1]
    etiquetas_simetria = [r'$\Gamma$', r'$M$', r'$K$', r'$\Gamma$']
    
    # 4. Graficar
    plt.figure(figsize=(9, 6))
    plt.plot(x_vals, bandas[:, 0], label='Banda 1', color='#1f77b4', linewidth=2)
    plt.plot(x_vals, bandas[:, 1], label='Banda 2', color='#ff7f0e', linewidth=2)
    plt.plot(x_vals, bandas[:, 2], label='Banda 3', color='#2ca02c', linewidth=2)
    
    # Formateo estético de la gráfica
    plt.title('Estructura de Bandas del Modelo Tight-Binding', fontsize=16)
    plt.ylabel('Energía (eV)', fontsize=14)
    plt.xlim(0, len(x_vals)-1)
    
    # Reemplazar los números del eje X con las letras de los puntos de simetría
    plt.xticks(puntos_simetria, etiquetas_simetria, fontsize=14)
    
    # Dibujar líneas verticales en los puntos de alta simetría
    for pt in puntos_simetria:
        plt.axvline(x=pt, color='black', linestyle='--', linewidth=1, alpha=0.5)
        
    # Dibujar línea horizontal en E=0 (Nivel de Fermi de referencia)
    plt.axhline(y=0, color='gray', linestyle='-', linewidth=1, alpha=0.5)

    plt.legend(loc='best', fontsize=12)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    plot_estructura_bandas()
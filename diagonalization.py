import numpy as np
import matplotlib.pyplot as plt




def calcular_H_numerica(a, b, params):
    """Construye la matriz Hamiltoniana 3x3 para valores dados de alfa (a) y beta (b)."""
    e1, e2, e3 = params['e1'], params['e2'], params['e3']
    t0, t1, t11,t2, t22, t12 = params['t0'], params['t1'], params['t11'], params['t2'], params['t22'], params['t12']
    
    H = np.zeros((3, 3), dtype=complex)
    
    # Elementos de la diagonal
    H[0, 0] = e1 + 2*t0*(np.cos(2*a) + 2*np.cos(a)*np.cos(b))
    H[1, 1] = e2 + 2*t11*np.cos(2*a) + (t11 + 3*t22)*np.cos(a)*np.cos(b)
    H[2, 2] = e3 + 2*t22*np.cos(2*a) + (3*t11 + t22)*np.cos(a)*np.cos(b)
    
    # Elementos fuera de la diagonal (H12 y su conjugado)  h1
    H[0, 1] = -2*t2*np.sqrt(3)*np.sin(a)*np.sin(b) +2*1j*t1*(  np.sin(2*a) + np.sin(a)*np.cos(b) )    
    H[1, 0] = np.conj(H[0, 1])
    
    # Elementos fuera de la diagonal (H13 y su conjugado) h2
    H[0, 2] = 2*t2*(  np.cos(2*a) - np.cos(a)*np.cos(b)  ) + 2j*np.sqrt(3)*t1*np.cos(a)*np.sin(b)
    H[2, 0] = np.conj(H[0, 2])  
    
    # Elementos fuera de la diagonal (H23 y su conjugado) h12
    H[1, 2] = np.sqrt(3 ) *( t22-t11 ) *np.sin(a)*np.sin(b) +4j*t12*np.sin(a)*( np.cos(a) - np.cos(b) )
    H[2, 1] = np.conj(H[1, 2])
    
    return H

def plot_estructura_bandas():
    # 1. Parámetros físicos (Según tus notas)
    parametros = {
        'e1': 1.046, 'e2': 2.104, 'e3': 2.104,  # Energías de sitio (e11, e22, e33)
        't0': -0.184, 't1':0.401, 't2': 0.507,                         # Salto t_0
        't11': 0.218,'t12': 0.338 , 't22': 0.057,        # Saltos t_11 y t_22
    }
    
    # 2. Definir los tramos del camino en el espacio k
    N = 1000 # Número de puntos por tramo
    
    # Tramo 1: Gamma -> K

    alpha_GK = np.linspace(0, 2*np.pi/(3), N)
    beta_GK = np.zeros(N) 

    # Tramo 1: K -> M

    alpha_KM = np.linspace(0, 2*np.pi/(3), N)
    beta_KM = np.zeros(N) 

    
    # Concatenar todos los tramos en un solo arreglo continuo
    alpha_vals = np.concatenate([alpha_GK, alpha_KM])
    beta_vals = np.concatenate([beta_GK, beta_KM])
    
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
    etiquetas_simetria = [r'$\Gamma$', r'$K$', r'$M$', r'$\Gamma$']
    
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
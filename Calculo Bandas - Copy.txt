import numpy as np
import matplotlib.pyplot as plt

def Hamiltonian(a, b, params):

    e1, e2, e3 = params['e1'], params['e2'], params['e3']
    t0, t1, t11, t2, t22, t12 = params['t0'], params['t1'], params['t11'], params['t2'], params['t22'], params['t12']
    
    H = np.zeros((3, 3), dtype=complex)
    
    # Elementos de la diagonal
    H[0, 0] = e1 + 2*t0*(np.cos(2*a) + 2*np.cos(a)*np.cos(b))
    H[1, 1] = e2 + 2*t11*np.cos(2*a) + (t11 + 3*t22)*np.cos(a)*np.cos(b)
    H[2, 2] = e3 + 2*t22*np.cos(2*a) + (3*t11 + t22)*np.cos(a)*np.cos(b)
    
    # Elementos fuera de la diagonal (H12 y su conjugado)  h1
    H[0, 1] = -2*t2*np.sqrt(3)*np.sin(a)*np.sin(b) + 2*1j*t1*(np.sin(2*a) + np.sin(a)*np.cos(b))    
    H[1, 0] = np.conj(H[0, 1])
    
    # Elementos fuera de la diagonal (H13 y su conjugado) h2
    H[0, 2] = 2*t2*(np.cos(2*a) - np.cos(a)*np.cos(b)) + 2j*np.sqrt(3)*t1*np.cos(a)*np.sin(b)
    H[2, 0] = np.conj(H[0, 2])  
    
    # Elementos fuera de la diagonal (H23 y su conjugado) h12
    H[1, 2] = np.sqrt(3)*(t22 - t11)*np.sin(a)*np.sin(b) + 4j*t12*np.sin(a)*(np.cos(a) - np.cos(b))
    H[2, 1] = np.conj(H[1, 2])
    
    return H

def Bandas(a_vals, b_vals, parametros):
    """Calcula las bandas para toda la ruta dada una serie de parametros"""
    bandas = []
    for a, b in zip(a_vals, b_vals):
        H_num = Hamiltonian(a, b, parametros)
        eigenvalores = np.linalg.eigvalsh(H_num)
        bandas.append(eigenvalores)
    return np.array(bandas)

def Plot_bandas():

    GGA = {
        'e1': 1.046, 'e2': 2.104, 'e3': 2.104,  
        't0': -0.184, 't1': 0.401, 't2': 0.507, 
        't11': 0.218, 't12': 0.338, 't22': 0.057
    }
    
    LDA = {
        'e1': 1.238, 'e2': 2.366, 'e3': 2.366,  
        't0': -0.218, 't1': 0.444, 't2': 0.533, 
        't11': 0.250, 't12': 0.360, 't22': 0.047
    }

    # 2. Distancias físicas en el espacio recíproco
    dist_GK = 4 * np.pi / 3          
    dist_KM = 2 * np.pi / 3          
    dist_MG = 2 * np.pi / np.sqrt(3) 
    
    N = 1000 # Resolución
    
    # 3. Construir los caminos
    alpha_GK = np.linspace(0, np.pi/3, N)
    beta_GK = np.linspace(0, np.pi, N)
    x_GK = np.linspace(0, dist_GK, N)
    
    alpha_KM = np.linspace(np.pi/3, 0, N)
    beta_KM = np.full(N, np.pi)
    x_KM = np.linspace(dist_GK, dist_GK + dist_KM, N)
    
    alpha_MG = np.zeros(N)
    beta_MG = np.linspace(np.pi, 0, N)
    x_MG = np.linspace(dist_GK + dist_KM, dist_GK + dist_KM + dist_MG, N)
    
    a_vals = np.concatenate([alpha_GK, alpha_KM, alpha_MG])
    b_vals = np.concatenate([beta_GK, beta_KM, beta_MG])
    x_vals = np.concatenate([x_GK, x_KM, x_MG])
    
    # 4. Diagonalización 
    bandas_gga = Bandas(a_vals, b_vals, GGA)
    bandas_lda = Bandas(a_vals, b_vals, LDA)
    
    # 5. Configuración de Etiquetas del Eje X
    puntos_simetria = [0, dist_GK, dist_GK + dist_KM, dist_GK + dist_KM + dist_MG]
    etiquetas = [r'$\Gamma$', r'$K$', r'$M$', r'$\Gamma$']
    
    # 6. Graficar
    plt.figure(figsize=(10, 7))
    
    # Graficar GGA (Líneas rojas sólidas) - Solo ponemos label en la primera para que no se repita en la leyenda
    plt.plot(x_vals, bandas_gga[:, 0], color='red', linestyle='-', linewidth=2, label='MoS$_2$ (GGA)')
    plt.plot(x_vals, bandas_gga[:, 1], color='red', linestyle='-', linewidth=2)
    plt.plot(x_vals, bandas_gga[:, 2], color='red', linestyle='-', linewidth=2)

    # Graficar LDA (Líneas azules punteadas)
    plt.plot(x_vals, bandas_lda[:, 0], color='blue', linestyle='--', linewidth=2, label='MoS$_2$ (LDA)')
    plt.plot(x_vals, bandas_lda[:, 1], color='blue', linestyle='--', linewidth=2)
    plt.plot(x_vals, bandas_lda[:, 2], color='blue', linestyle='--', linewidth=2)
    
    # Estilos del gráfico
    plt.title(r'Comparación de Bandas MoS$_2$: Ruta $\Gamma \rightarrow K \rightarrow M \rightarrow \Gamma$', fontsize=16, pad=15)
    plt.ylabel(r'$E(\mathbf{k})$ (eV)', fontsize=14)
    plt.xlim(0, x_vals[-1])
    

    plt.xticks(puntos_simetria, etiquetas, fontsize=14)
    
    for pt in puntos_simetria:
        plt.axvline(x=pt, color='black', linestyle='--', linewidth=1, alpha=0.5)
    plt.axhline(y=0, color='gray', linestyle='-', linewidth=1, alpha=0.5)
    
    plt.legend(fontsize=12, loc='upper right')
    plt.tight_layout()
    
    plt.show()


if __name__ == "__main__":
    Plot_bandas()
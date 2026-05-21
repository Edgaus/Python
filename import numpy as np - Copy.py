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
        'e1': 1.238, 'e2': 2.366, 'e3': 2.366,  # Energías de sitio (e11, e22, e33)
        't0': -0.218, 't1': 0.444, 't2': 0.533,                         # Salto t_0
        't11': 0.250,'t12': 0.360 , 't22': 0.047,        # Saltos t_11 y t_22
    }
    


      # 2. Distancias físicas en el espacio recíproco para la nueva ruta
    dist_GK = 4 * np.pi / 3          # Distancia de Gamma a K
    dist_KM = 2 * np.pi / 3          # Distancia de K a M
    dist_MG = 2 * np.pi / np.sqrt(3) # Distancia de M a Gamma
    
    N = 150 # Resolución por tramo
    
    # 3. Construir los caminos
    
    # Tramo 1: Gamma -> K (ambas variables aumentan)
    alpha_GK = np.linspace(0, np.pi/3, N)
    beta_GK = np.linspace(0, np.pi, N)
    x_GK = np.linspace(0, dist_GK, N)
    
    # Tramo 2: K -> M (beta constante, alpha disminuye)
    alpha_KM = np.linspace(np.pi/3, 0, N)
    beta_KM = np.full(N, np.pi)
    x_KM = np.linspace(dist_GK, dist_GK + dist_KM, N)
    
    # Tramo 3: M -> Gamma (alpha constante, beta disminuye)
    alpha_MG = np.zeros(N)
    beta_MG = np.linspace(np.pi, 0, N)
    x_MG = np.linspace(dist_GK + dist_KM, dist_GK + dist_KM + dist_MG, N)
    
    # Concatenar todos los tramos
    a_vals = np.concatenate([alpha_GK, alpha_KM, alpha_MG])
    b_vals = np.concatenate([beta_GK, beta_KM, beta_MG])
    x_vals = np.concatenate([x_GK, x_KM, x_MG])
    
    # 4. Diagonalización numérica
    bandas = []
    for a, b in zip(a_vals, b_vals):
        H_num = calcular_H_numerica(a, b, parametros)
        eigenvalores = np.linalg.eigvalsh(H_num)
        bandas.append(eigenvalores)
        
    bandas = np.array(bandas)
    
    # 5. Configuración de Etiquetas del Eje X para la nueva ruta
    puntos_simetria = [0, dist_GK, dist_GK + dist_KM, dist_GK + dist_KM + dist_MG]
    etiquetas = [
        r'$\Gamma$', 
        r'$K$', 
        r'$M$', 
        r'$\Gamma$'
    ]
    
    # 6. Graficar
    plt.figure(figsize=(9, 6))
    
    plt.plot(x_vals, bandas[:, 0], color='#1f77b4', linewidth=2.5)
    plt.plot(x_vals, bandas[:, 1], color='#1f77b4', linewidth=2.5)
    plt.plot(x_vals, bandas[:, 2], color='#1f77b4', linewidth=2.5)
    
    plt.title(r'Estructura de Bandas: Ruta $\Gamma \rightarrow K \rightarrow M \rightarrow \Gamma$', fontsize=16, pad=15)
    plt.ylabel(r'$E(\mathbf{k})$ (eV)', fontsize=14)
    plt.xlim(0, x_vals[-1])
    plt.ylim(-4, 4) 
    
    plt.xticks(puntos_simetria, etiquetas, fontsize=14)
    
    for pt in puntos_simetria:
        plt.axvline(x=pt, color='black', linestyle='--', linewidth=1, alpha=0.5)
    plt.axhline(y=0, color='gray', linestyle='-', linewidth=1, alpha=0.5)
    
    plt.tight_layout()
    plt.show()
    # --- BLOQUE PARA GUARDAR DATOS ---
    # Creamos una matriz donde la primera columna es el eje X y las siguientes son las energías
    datos_a_guardar = np.column_stack((x_vals, bandas[:, 0], bandas[:, 1], bandas[:, 2]))
    
    # Guardamos en un archivo .txt
    # 'fmt' define el número de decimales, 'header' añade los nombres de las columnas
    np.savetxt('estructura_bandas_LDA.txt', datos_a_guardar, 
               fmt='%.8e', 
               header='Eje_X_Distancia Banda_1 Banda_2 Banda_3',
               comments='')
    
    print("¡Datos guardados exitosamente en 'estructura_bandas_LDA.txt'!")
    # ---------------------------------
if __name__ == "__main__":
    plot_estructura_bandas()
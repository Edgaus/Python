import sympy as sp
import re # IMPORTANTE: Importamos el módulo para editar el texto final

def acomodar_fracciones(match):
    """
    Esta función toma los pedazos de la fracción que encuentra Python
    y los reordena para sacar el t_{ij} del numerador.
    """
    prefijo_numerador = match.group(1).strip() # Ej: '\sqrt{3}' o ''
    variable_t = match.group(2)                # Ej: 't_{01c}'
    denominador = match.group(3)               # Ej: '2' o '4'
    
    # Si no hay nada acompañando a la variable en el numerador, ponemos un 1
    if prefijo_numerador == "":
        prefijo_numerador = "1"
    elif prefijo_numerador == "-":
        prefijo_numerador = "-1"
        
    # Devolvemos el texto reacomodado: \frac{numerador}{denominador} t_{ij}
    return rf"\frac{{{prefijo_numerador}}}{{{denominador}}} {variable_t}"


def multiply_and_export_latex():
    # 1. Definir los símbolos
    t00, t01, t02, t01_c, t11, t12, t02_c, t_12_c, t22 = sp.symbols('t_{00} t_{01} t_{02} t_{01c} t_{11} t_{12} t_{02c} t_{12c} t_{22}')

    # 2. Definir la Matriz A
    matrix_A = sp.Matrix([
        [t00,   t01,    t02],
        [-t01_c, t11,    t12],
        [t02_c, -t_12_c, t22]
    ])

    # 3. Definir la Matriz B 
    matrix_cv_prime = sp.Matrix([
        [1, 0,                  0],
        [0, sp.Rational(1, 2),  sp.sqrt(3)/2],
        [0, sp.sqrt(3)/2,       sp.Rational(-1, 2)]
    ])


    matrix_cv_biprime = sp.Matrix([
        [1, 0,                  0],
        [0, sp.Rational(1, 2),  -sp.sqrt(3)/2],
        [0, -sp.sqrt(3)/2,       sp.Rational(-1, 2)]
    ])

    matrix_C_2 = sp.Matrix([
        [1, 0,                  0],
        [0, sp.Rational(-1, 2),  -sp.sqrt(3)/2],
        [0, sp.sqrt(3)/2,       sp.Rational(-1, 2)]
    ])


    matrix_C = sp.Matrix([
        [1, 0,                  0],
        [0, sp.Rational(-1, 2),  sp.sqrt(3)/2],
        [0, -sp.sqrt(3)/2,       sp.Rational(-1, 2)]
    ])





    # 4. Multiplicación de matrices (D * H * D^\dagger)
    result_matrix = matrix_cv_biprime * matrix_A * matrix_cv_biprime

    # CAMBIO CLAVE: Usamos expand() para evitar que SymPy agrupe sumas en una sola fracción
    expanded_result = sp.expand(result_matrix)

    # 5. Convertir a LaTeX
    latex_string = sp.latex(expanded_result)

    # 6. Reacomodar las fracciones en el texto generado
    # Busca fracciones que terminen en t_{algo} dentro del numerador
    patron_fraccion = r"\\frac\{(.*?)(t_\{.*?\})\}\{(.*?)\}"
    latex_final = re.sub(patron_fraccion, acomodar_fracciones, latex_string)

    print("--- Copia el texto debajo en tu editor LaTeX ---")
    print(latex_final)

if __name__ == "__main__":
    multiply_and_export_latex()
# Reto Salud Digna
En este repositorio se encuentran todos los códigos necesarios e implementaciones desarrolladas para dar solución a dos problemas actuales que enfrenta Salud Digna. Cada solución ha sido diseñada con base en el análisis de datos reales y se encuentra documentada para facilitar su comprensión, reproducción y futura mejora. El repositorio está organizado de manera que permite acceder fácilmente a los scripts, funciones y resultados asociados a cada problema abordado.

Salud Digna es una organización sin fines de lucro que busca proveer servicios de la salud, como pruebas y exámenes médicos, a precios accesibles. Una empresa que tiene presencia en muchos países de Latinoamérica y cuentan con clínicas pequeñas (que tienen el equipo básico), clínicas medianas y clínicas grandes. Su enfoque es proveer servicios de salud a precio accesible y de forma rápida.

# Problemáticas
## Fila de espera
En Salud Digna, se otorga prioridad de atención a mujeres embarazadas y personas de la tercera edad. Sin embargo, durante los horarios de alta demanda, este enfoque provoca largos tiempos de espera para el resto de los pacientes. El algoritmo actual prioriza exclusivamente a los grupos vulnerables y no considera criterios de equidad o eficiencia para los demás usuarios. Como resultado, pacientes sin prioridad pueden esperar horas para ser atendidos, lo cual afecta negativamente su experiencia y la eficiencia operativa de la clínica.

## Ruta óptima 
Muchos pacientes acuden a Salud Digna para realizarse múltiples estudios clínicos en una sola visita. Debido a que la disponibilidad de los laboratorios varía según el tipo de análisis y la hora del día, los pacientes suelen enfrentarse a múltiples filas y tiempos muertos entre cada prueba. Esto genera recorridos poco eficientes dentro de la clínica, provocando que una visita que podría ser breve se convierta en una experiencia de varias horas. Esta problemática impacta tanto la satisfacción del paciente como la capacidad de atención diaria del centro.

# Objetivos
## Fila de espera
Diseñar e implementar un sistema de atención que garantice que ningún paciente espere más de 20 minutos, manteniendo la prioridad para mujeres embarazadas y personas de la tercera edad. La solución debe ser escalable y adaptable a diferentes niveles de demanda en las sucursales.

## Ruta óptima 
Determinar y recomendar la ruta óptima que cada paciente debe seguir dentro de la clínica para minimizar su tiempo total de permanencia, considerando la disponibilidad de servicios y la secuencia de estudios requeridos. La solución debe ser escalable y adaptable a diferentes configuraciones operativas.

# Estructura del repositorio
- **data**  
    Conjuntos de datos utilizados para el análisis y simulaciones.

- **Gráficas**  
    Visualizaciones generadas durante el análisis de datos y validación de modelos.
  
- **Reportes**  
    Reportes técnicos y ejecutivos sobre hallazgos relevantes en los datos.

- **Fila de espera**  
    Implementación y simulación de la solución para reducir los tiempos de espera, priorizando a grupos vulnerables.

- **Ruta optima**  
    Resultados y desarrollo del modelo que recomienda la mejor secuencia de estudios para minimizar el tiempo total de permanencia del paciente. 

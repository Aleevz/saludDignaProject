# -*- coding: utf-8 -*-
"""
Created on Tue May 27 10:43:07 2025

@author: Equipo 6
"""
import numpy as np
import pandas as pd
from datetime import timedelta

class Paciente:
    def __init__(self, id, sucursal, hora_llegada, prioridad, tiempo_estimado):
        self.id = id
        self.sucursal = sucursal
        self.hora_llegada = hora_llegada
        self.prioridad_inicial = prioridad  # 0 = más alta
        self.tiempo_estimado = tiempo_estimado

    def calcular_puntaje(self, hora_actual):
        espera = (hora_actual - self.hora_llegada).total_seconds() / 60
        return self.prioridad_inicial * 15 + espera * 3

# Función para seleccionar siguiente paciente con prioridad dinámica

def seleccionar_siguiente_paciente(cola, hora_actual):
    pacientes_largos = [p for p in cola if (hora_actual - p.hora_llegada) >= timedelta(minutes=20)]
    if pacientes_largos:
        return max(pacientes_largos, key=lambda p: p.calcular_puntaje(hora_actual))
    elif cola:
        return max(cola, key=lambda p: p.calcular_puntaje(hora_actual))
    return None


# Función para simular atención a pacientes con cajas por sucursal

def simular_atencion(df_sim, cajas):
    resultados = []
    # Crear objetos Paciente
    pacientes = [
        Paciente(
            id=i,
            sucursal=row["Sucursal"],
            hora_llegada=row["FechaHoraSimulada"],
            prioridad=row["Prioridad"],
            tiempo_estimado=row["TAPRecepcionMinutos"]


        )
        for i, row in df_sim.iterrows()
    ]

    cola = pacientes.copy()
    tiempo_actual = min(p.hora_llegada for p in cola)

    # Inicializar disponibilidad de cada caja (todas libres desde la hora inicial)
    disponibilidad_cajas = [tiempo_actual for _ in range(cajas)]

    while cola:
        # Ver qué cajas están disponibles en este momento
        cajas_libres = [i for i, libre_hasta in enumerate(disponibilidad_cajas) if libre_hasta <= tiempo_actual]
        
        # Filtrar pacientes que ya llegaron
        pacientes_actuales = [p for p in cola if p.hora_llegada <= tiempo_actual]

        for i_caja in cajas_libres:
            if not pacientes_actuales:
                break
            # Seleccionar paciente con prioridad dinámica
            siguiente = seleccionar_siguiente_paciente(pacientes_actuales, tiempo_actual)
            if siguiente:
                hora_inicio = max(tiempo_actual, siguiente.hora_llegada)
                espera = (hora_inicio - siguiente.hora_llegada).total_seconds() / 60

                print(f"{hora_inicio.time()} | Caja {i_caja + 1} atiende ID {siguiente.id} "
                      f"(Prioridad {siguiente.prioridad_inicial}) - Espera: {espera:.1f} min")
                
                # Actualizar disponibilidad de la caja
                disponibilidad_cajas[i_caja] = hora_inicio + timedelta(minutes=siguiente.tiempo_estimado)
                
                resultados.append({
                        "id": siguiente.id,
                        "prioridad": siguiente.prioridad_inicial,
                        "hora_llegada": siguiente.hora_llegada,
                        "hora_inicio": tiempo_actual,
                        "espera_min": espera,
                        "caja": i_caja + 1
                    })
                
                # Eliminar paciente de la cola
                cola.remove(siguiente)
                pacientes_actuales.remove(siguiente)

        tiempo_actual += timedelta(minutes=1)
        df_resultados = pd.DataFrame(resultados)
    return df_resultados

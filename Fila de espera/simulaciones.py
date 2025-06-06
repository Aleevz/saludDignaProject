# -*- coding: utf-8 -*-
"""
Created on Tue May 27 10:38:20 2025

@author: Equipo 6
"""

import numpy as np
import pandas as pd
from datetime import timedelta


def simulacion_pacientes(sucursal, df,fechabase):
    df_sucursal = df[df["Sucursal"] == sucursal].copy()

    # Calcular llegadas promedio por hora del día (0-23)
    llegadas_por_hora_promedio = (
        df_sucursal.groupby(df_sucursal["FechaHoraLLegada"].dt.hour)
        .size()
        / df_sucursal["FechaHoraLLegada"].dt.date.nunique()
    )
    
    # Simulación por minuto usando distribución multinomial

    horas = np.arange(6, 18)
    simulacion_minuto_a_minuto = {}

    for hora in horas:
        tasa_hora = llegadas_por_hora_promedio.get(hora, 0)
        llegadas_totales = np.random.poisson(tasa_hora)
        llegadas_minuto = np.random.multinomial(llegadas_totales, [1/60]*60)
        simulacion_minuto_a_minuto[hora] = llegadas_minuto

    # Crear DataFrame simulado con timestamps
   
    fecha_base = pd.to_datetime(fechabase)  # Día simulado
    sim_llegadas = []

    for hora, minutos in simulacion_minuto_a_minuto.items():
        for minuto, llegadas in enumerate(minutos):
            for _ in range(llegadas):
                timestamp = fecha_base + timedelta(hours=int(hora), minutes=int(minuto))
                sim_llegadas.append({
                    "Sucursal": sucursal,
                    "FechaHoraSimulada": timestamp
                })

    df_sim = pd.DataFrame(sim_llegadas)

    
    # Distribución real de prioridad
    prioridades = df_sucursal["Prioridad"].value_counts(normalize=True)
    df_sim["Prioridad"] = np.random.choice(
        prioridades.index,
        size=len(df_sim),
        p=prioridades.values
    )

    # Tiempo de atención basado en datos reales
    df_sim["TAPRecepcionMinutos"] = np.random.choice(
        df_sucursal["TAPRecepcionMinutos"].dropna(),
        size=len(df_sim)
    )
    return df_sim
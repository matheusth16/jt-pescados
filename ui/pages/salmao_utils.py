"""
Utilitários para a página de salmão.
"""
import pandas as pd
import streamlit as st


@st.cache_data(show_spinner=False)
def preparar_dataframe_view(df_input):
    """
    Limpeza e conversão de tipos do DataFrame para exibição.
    Cacheado para evitar reprocessamento a cada rerun.
    """
    if df_input.empty:
        return df_input

    df_view = df_input.copy()

    cols_texto = ["Calibre", "Cliente", "Fornecedor"]
    for c in cols_texto:
        if c in df_view.columns:
            df_view[c] = df_view[c].fillna("").astype(str).replace("None", "").replace("nan", "")

    if "Status" in df_view.columns:
        df_view["Status"] = (
            df_view["Status"]
            .fillna("Livre")
            .astype(str)
            .replace("None", "Livre")
            .replace("nan", "Livre")
            .replace("", "Livre")
        )

    if "Peso" in df_view.columns:
        df_view["Peso"] = pd.to_numeric(df_view["Peso"], errors="coerce").fillna(0.0)

    if "Validade" in df_view.columns:
        df_view["Validade"] = pd.to_datetime(df_view["Validade"], format="%d/%m/%Y", errors="coerce")

    return df_view

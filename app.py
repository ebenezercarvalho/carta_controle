import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import io
from fpdf import FPDF
import base64
from pathlib import Path
import tempfile
import logging
import re
import gettext
import os
import pkg_resources

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração da página
st.set_page_config(
    page_title="SigmaTrack - Gerador de Carta de Controle",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Inserir logo
st.image('img/logo.png', width=200)

# Estilo CSS personalizado
st.markdown("""
<style>
    .stTextInput > div > div > input {
        border-radius: 10px;
    }
    .stButton > button {
        border-radius: 10px;
        transition: all 0.3s ease;
        width: auto !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    .css-1d391kg {
        border-radius: 10px;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    .stPlotlyChart {
        width: 100%;
    }
    .streamlit-expanderHeader {
        font-size: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def format_date(date):
    return date.strftime('%d/%m/%Y')

def validate_data(df):
    required_columns = ['Data', 'Valor']
    if not all(col in df.columns for col in required_columns):
        raise ValueError("O arquivo deve conter as colunas 'Data' e 'Valor'")
    
    try:
        pd.to_datetime(df['Data'])
    except ValueError:
        raise ValueError("Formato de data inválido. Use o formato aaaa-mm-dd.")
    
    if not np.issubdtype(df['Valor'].dtype, np.number):
        raise ValueError("A coluna 'Valor' deve conter apenas números.")

@st.cache_data
def process_data(data_str):
    try:
        df = pd.read_csv(io.StringIO(data_str))
        if len(df.columns) != 2:
            raise ValueError("O arquivo deve conter exatamente 2 colunas")
        df.columns = ['Data', 'Valor']
        
    except:
        lines = data_str.strip().split('\n')
        dates = []
        values = []
        start_idx = 1 if ('data' in lines[0].lower() or 'valor' in lines[0].lower()) else 0
        
        for line in lines[start_idx:]:
            if ',' in line:
                date_str, value_str = line.strip().split(',')
                dates.append(date_str)
                values.append(float(value_str))
        
        df = pd.DataFrame({
            'Data': dates,
            'Valor': values
        })
    
    validate_data(df)
    df['Data'] = pd.to_datetime(df['Data'])
    df['Valor'] = df['Valor'].astype(float)
    return df

def create_report(nome_analise, data_atual, fig, mean, std, n_samples):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
        fig.write_image(tmp_file.name)
        img_path = tmp_file.name

    class PDF(FPDF):
        def __init__(self):
            super().__init__()
            self.set_auto_page_break(auto=True, margin=15)
            
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    
    # Título
    pdf.cell(0, 10, f"Relatório de Carta Controle - {nome_analise}", ln=True, align='C')
    pdf.ln(10)
    
    # Informações gerais
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f"Gerado em: {data_atual}", ln=True)
    pdf.cell(0, 10, f"Número de amostras: {n_samples}", ln=True)
    pdf.cell(0, 10, f"Média: {mean:.2f}", ln=True)
    pdf.cell(0, 10, f"Desvio padrão: {std:.2f}", ln=True)
    pdf.ln(10)
    
    # Gráfico
    pdf.image(img_path, x=10, w=190)
    
    # Gerar PDF em bytes
    pdf_bytes = bytes(pdf.output(dest='S'))
    
    # Limpar arquivo temporário
    Path(img_path).unlink()
    
    return pdf_bytes

# Interface principal
st.title("SigmaTrack - Carta Controle")

# Informações do relatório
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        nome_analise = st.text_input("Nome da análise", "Análise de Processo")
    with col2:
        data_atual = st.date_input("Data do relatório", datetime.now())

# Instruções
with st.expander("Como usar", expanded=False):
    st.markdown("""
    1. Escolha entre colar os dados ou fazer upload de um arquivo CSV
    2. Os dados devem ter duas colunas: data e valor
    3. As datas devem estar na primeira coluna (formato: aaaa-mm-dd)
    4. Os valores numéricos na segunda coluna
    
    Exemplo de formato:
    ```
    Data,Valor
    2025-01-01,25
    2025-01-02,10
    2025-01-03,12
    ```
    """)

# Entrada de dados
input_method = st.radio(
    "Escolha como deseja inserir os dados:",
    ["Colar dados", "Carregar arquivo CSV"]
)

df = None

if input_method == "Colar dados":
    input_data = st.text_area(
        "Cole seus dados aqui:",
        height=150
    )
    if input_data:
        try:
            df = process_data(input_data)
            with st.expander("Pré-visualização dos dados", expanded=False):
                st.dataframe(df.head())
        except Exception as e:
            st.error(f"Erro ao processar os dados: {str(e)}")
else:
    uploaded_file = st.file_uploader("Escolha um arquivo CSV", type=['csv'])
    if uploaded_file is not None:
        try:
            df = process_data(uploaded_file.getvalue().decode('utf-8'))
            with st.expander("Pré-visualização dos dados", expanded=False):
                st.dataframe(df.head())
        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {str(e)}")

# Botão para gerar o gráfico
if st.button("Gerar Carta de Controle"):
    if df is not None:
        try:
            # Preparar dados
            df['Data_Formatada'] = df['Data'].apply(format_date)
            mean = df['Valor'].mean()
            std = df['Valor'].std()
            
            # Calcular limites
            ucl3 = mean + 3*std
            ucl2 = mean + 2*std
            ucl1 = mean + 1*std
            lcl3 = mean - 3*std
            lcl2 = mean - 2*std
            lcl1 = mean - 1*std
            
            # Criar gráfico
            fig = go.Figure()
            
            # Linha de dados
            fig.add_trace(go.Scatter(
                x=df['Data_Formatada'],
                y=df['Valor'],
                mode='lines+markers',
                name='Valores',
                line=dict(color="#1f77b4", width=2),
                marker=dict(size=8)
            ))
            
            # Linhas de controle
            fig.add_hline(y=mean, line_dash="dash", line_color="green",
                         annotation_text="Média", annotation_position="right")
            
            # Limites superiores
            fig.add_hline(y=ucl3, line_dash="dot", line_color="red",
                         annotation_text="+3σ", annotation_position="right")
            fig.add_hline(y=ucl2, line_dash="dot", line_color="orange",
                         annotation_text="+2σ", annotation_position="right")
            fig.add_hline(y=ucl1, line_dash="dot", line_color="yellow",
                         annotation_text="+1σ", annotation_position="right")
            
            # Limites inferiores
            fig.add_hline(y=lcl3, line_dash="dot", line_color="red",
                         annotation_text="-3σ", annotation_position="right")
            fig.add_hline(y=lcl2, line_dash="dot", line_color="orange",
                         annotation_text="-2σ", annotation_position="right")
            fig.add_hline(y=lcl1, line_dash="dot", line_color="yellow",
                         annotation_text="-1σ", annotation_position="right")
            
            # Layout
            fig.update_layout(
                title={
                    'text': "Carta de Controle",
                    'y': 0.95,
                    'x': 0.5,
                    'xanchor': 'center',
                    'yanchor': 'top'
                },
                xaxis_title="Data",
                yaxis_title="Valor",
                hovermode='x unified',
                showlegend=True,
                template='plotly_white',
                height=600,
                margin=dict(l=50, r=50, t=50, b=50)
            )
            
            # Exibir gráfico
            st.plotly_chart(fig, use_container_width=True)
            
            # Exibir estatísticas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Média", f"{mean:.2f}")
            with col2:
                st.metric("Desvio Padrão", f"{std:.2f}")
            with col3:
                st.metric("Número de Amostras", len(df))
            
            # Gerar e disponibilizar PDF
            pdf_bytes = create_report(
                nome_analise,
                data_atual.strftime('%d/%m/%Y'),
                fig,
                mean,
                std,
                len(df)
            )
            
            st.download_button(
                label="📥 Baixar Relatório PDF",
                data=pdf_bytes,
                file_name=f"relatorio_carta_controle_{nome_analise}_{data_atual.strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
            
        except Exception as e:
            st.error(f"Erro ao gerar o gráfico: {str(e)}")
    else:
        st.warning("Por favor, insira alguns dados para gerar o gráfico.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>Desenvolvido por Ebenézer Carvalho</p>
</div>
""", unsafe_allow_html=True)

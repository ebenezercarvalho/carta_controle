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
from pathlib import Path
import os

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração da página
st.set_page_config(
    page_title="Carta de Controle",
    #page_icon="📊",
    layout="wide"
)

# Estilo CSS personalizado
st.markdown("""
<style>
    .stTextInput > div > div > input {
        border-radius: 10px;
    }
    .stButton > button {
        border-radius: 10px;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    .css-1d391kg {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Função para converter data para formato dd/mm/aaaa
def format_date(date):
    return date.strftime('%d/%m/%Y')

# Função para validar dados
def validate_data(df):
    try:
        pd.to_datetime(df['Data'], format='%Y-%m-%d')
    except ValueError:
        raise ValueError("Formato de data inválido. Use o formato aaaa-mm-dd.")
    if not np.issubdtype(df['Valor'].dtype, np.number):
        raise ValueError("A coluna 'Valor' deve conter apenas números.")

# Função para processar os dados
@st.cache_data  # Substituído st.cache por st.cache_data
def process_data(data_str):
    try:
        # Tentar ler como CSV com pandas
        df = pd.read_csv(io.StringIO(data_str))
        
        # Se temos mais ou menos que 2 colunas, raise error
        if len(df.columns) != 2:
            raise ValueError("O arquivo deve conter exatamente 2 colunas")
            
        # Renomear as colunas para padronizar
        df.columns = ['Data', 'Valor']
        
    except:
        # Se falhar, tentar processar linha por linha
        lines = data_str.strip().split('\n')
        dates = []
        values = []
        
        # Verificar se a primeira linha parece ser um cabeçalho
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
    
    # Validar dados
    validate_data(df)
    
    # Converter coluna de data
    df['Data'] = pd.to_datetime(df['Data'])
    # Converter valores para float
    df['Valor'] = df['Valor'].astype(float)
    
    return df

# Função para gerar o relatório PDF
def create_report(nome_analise, data_atual, fig, mean, std, n_samples):
    markdown_content = f"""# Relatório de Carta Controle - {nome_analise}
Gerado em {data_atual}

A Carta de Controle é uma ferramenta estatística fundamental para o monitoramento e controle de processos. Ela permite visualizar a variabilidade do processo ao longo do tempo e identificar possíveis anomalias ou tendências que necessitam de atenção.
## Conceitos Importantes
### Média
A média ({mean:.2f}) representa o valor central do processo. É calculada somando-se todos os valores e dividindo pelo número total de observações. A linha central no gráfico representa este valor.
### Desvios Padrão
O desvio padrão ({std:.2f}) é uma medida da variabilidade do processo. As linhas no gráfico representam:
- ±1σ: 68,27% dos dados devem estar nesta faixa
- ±2σ: 95,45% dos dados devem estar nesta faixa
- ±3σ: 99,73% dos dados devem estar nesta faixa
## Análise dos Dados
- Número de amostras analisadas: {n_samples}
- Média do processo: {mean:.2f}
- Desvio padrão: {std:.2f}

## Gráfico de Controle

Este relatório foi gerado automaticamente pelo sistema de Cartas de Controle.

Assinatura: _________________________________
Data: _______________________________________
"""

    # Criar arquivo temporário para o gráfico
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
        fig.write_image(tmp_file.name)
        img_path = tmp_file.name

    # Criar PDF usando FPDF com suporte a Unicode
    class PDF(FPDF):
        def __init__(self):
            super().__init__()
            # Definir o caminho absoluto para a pasta /fonts
            font_path = os.path.join(os.path.dirname(__file__), 'fonts')
            # Adicionar as variantes da fonte DejaVuSans
            self.add_font('DejaVuSans', '', os.path.join(font_path, 'dvs.ttf'), uni=True)
            self.add_font('DejaVuSans', 'B', os.path.join(font_path, 'DejaVuSans-Bold.ttf'), uni=True)
            self.add_font('DejaVuSans', 'I', os.path.join(font_path, 'DejaVuSans-Oblique.ttf'), uni=True)
            self.set_font('DejaVuSans', '', 11)  # Definir a fonte padrão

        def header(self):
            self.set_font('DejaVuSans', 'B', 12)
            self.cell(0, 10, f'Relatório de Carta Controle - {nome_analise}', 0, 1, 'C')
            self.ln(10)

    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Dividir o markdown em linhas e adicionar ao PDF
    for line in markdown_content.split('\n'):
        if line.startswith('# '):
            pdf.set_font('DejaVuSans', 'B', 16)
            pdf.ln(10)
            pdf.cell(0, 10, line[2:], 0, 1)
            pdf.ln(5)
        elif line.startswith('## '):
            pdf.set_font('DejaVuSans', 'B', 14)
            pdf.ln(5)
            pdf.cell(0, 10, line[3:], 0, 1)
        elif line.startswith('### '):
            pdf.set_font('DejaVuSans', 'B', 12)
            pdf.cell(0, 10, line[4:], 0, 1)
        else:
            pdf.set_font('DejaVuSans', '', 11)
            pdf.multi_cell(0, 10, line)

        if '## Gráfico de Controle' in line:
            pdf.image(img_path, x=10, w=190)
            pdf.ln(5)

    # Salvar PDF em bytes usando latin1 (compatível com FPDF)
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    
    # Limpar arquivo temporário do gráfico
    Path(img_path).unlink()
    
    return pdf_bytes

# Título do aplicativo com estilo
st.title("Gerador de Carta Controle")

# Campos para relatório
with st.expander("Informações para o relatório", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        nome_analise = st.text_input("Nome da análise", "Análise de Processo")
    with col2:
        data_atual = st.date_input("Data do relatório", datetime.now())

# Explicação do uso
st.markdown("""
### Como usar:
1. Escolha entre colar os dados ou fazer upload de um arquivo CSV
2. Os dados devem ter duas colunas: data e valor
3. As datas devem estar na primeira coluna (formato: aaaa-mm-dd)
4. Os valores numéricos na segunda coluna
5. Clique em 'Gerar Carta de Controle'
            
Exemplo de formato:
```
Data,Valor
2025-01-01,25
2025-01-02,10
2025-01-03,12
```

""")

# Seleção do método de entrada de dados
input_method = st.radio(
    "Escolha como deseja inserir os dados:",
    ["Colar dados", "Carregar arquivo CSV"]
)

df = None

if input_method == "Colar dados":
    input_data = st.text_area(
        "Cole seus dados aqui (duas colunas separadas por vírgula):",
        height=200,
        help="Exemplo:\nData,Valor\n2025-01-01,25\n2025-01-02,10"
    )
    if input_data:
        try:
            df = process_data(input_data)
            st.write("Pré-visualização dos dados carregados:")
            st.dataframe(df.head())
        except Exception as e:
            st.error(f"Erro ao processar os dados colados: {str(e)}")
else:
    uploaded_file = st.file_uploader("Escolha um arquivo CSV", type=['csv'])
    if uploaded_file is not None:
        try:
            df = process_data(uploaded_file.getvalue().decode('utf-8'))
            st.write("Pré-visualização dos dados carregados:")
            st.dataframe(df.head())
        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {str(e)}")

# Botão para gerar o gráfico
if st.button("Gerar Carta de Controle", key="generate"):
    if df is not None:
        try:
            # Converter formato da data
            df['Data_Formatada'] = df['Data'].apply(format_date)
            
            # Calcular estatísticas
            mean = df['Valor'].mean()
            std = df['Valor'].std()
            
            # Calcular limites de controle
            ucl3 = mean + 3*std
            ucl2 = mean + 2*std
            ucl1 = mean + 1*std
            lcl3 = mean - 3*std
            lcl2 = mean - 2*std
            lcl1 = mean - 1*std
            
            # Criar gráfico com Plotly
            fig = go.Figure()
            
            # Adicionar linha de dados
            line_color =  "#1f77b4"
            fig.add_trace(go.Scatter(
                x=df['Data_Formatada'],
                y=df['Valor'],
                mode='lines+markers',
                name='Valores',
                line=dict(color=line_color, width=2),
                marker=dict(size=8)
            ))
            
            # Adicionar linhas de controle
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
            
            # Configurar layout
            fig.update_layout(
                title={
                    'text': "Carta de Controle",
                    'y':0.95,
                    'x':0.5,
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
            
            # Exibir o gráfico
            st.plotly_chart(fig, use_container_width=True)
            
            # Exibir estatísticas em colunas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Média", f"{mean:.2f}")
            with col2:
                st.metric("Desvio Padrão", f"{std:.2f}")
            with col3:
                st.metric("Número de Amostras", len(df))
            
            # Gerar relatório PDF
            pdf_bytes = create_report(
                nome_analise,
                data_atual.strftime('%d/%m/%Y'),
                fig,
                mean,
                std,
                len(df)
            )
            
            # Botão para download do relatório
            st.download_button(
                label="📥 Baixar Relatório PDF",
                data=pdf_bytes,
                file_name=f"relatorio_carta_controle_{nome_analise}_{data_atual.strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
                
        except Exception as e:
            st.error(f"""
            Erro ao gerar o gráfico. Erro específico: {str(e)}
            """)
    else:
        st.warning("Por favor, insira alguns dados para gerar o gráfico.")

# Adicionar footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>Desenvolvido por Ebenézer Carvalho</p>
</div>
""", unsafe_allow_html=True)

# Função para salvar feedback em um arquivo
def save_feedback(feedback):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("feedbacks.txt", "a") as f:
        f.write(f"{timestamp} - {feedback}\n")

# Feedback do usuário
st.sidebar.markdown("### Feedback")
feedback = st.sidebar.text_area("Deixe seu feedback aqui:", key="feedback_input")
if st.sidebar.button("Enviar Feedback"):
    if feedback:
        save_feedback(feedback)
        st.sidebar.success("Obrigado!")
    
    else:
        st.sidebar.error("Por favor, insira seu feedback antes de enviar.")
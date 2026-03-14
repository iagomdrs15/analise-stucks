import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import pytz

# 1. Configuração da Página
st.set_page_config(
    page_title="Dashboard SPX Express - Manaus",
    page_icon="📦",
    layout="wide"
)

# Definir Fuso Horário de Brasília
fuso_br = pytz.timezone('America/Sao_Paulo')
hoje_br = datetime.now(fuso_br).date()

# 2. Atualização Automática (2 minutos)
st_autorefresh(interval=120000, key="auto_refresh_dashboard")

# 3. Estilização CSS
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 4. Conexão e Carga de Dados
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1nZV5z9bPoBsi7Xi4PA_WMMQcry7eX1ljGA1c9iLVFW8/edit#gid=0"
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # ttl=120 garante que o cache expire em 2 minutos
    df = conn.read(spreadsheet=url, ttl=120)
    
    # Limpar nomes de colunas
    df.columns = df.columns.str.strip()
    
    # CORREÇÃO DO ERRO DE DATA:
    # dayfirst=True força o Pandas a entender que 14/03 é 14 de Março, não erro.
    df['Data Recebimento'] = pd.to_datetime(
        df['Data Recebimento'], 
        dayfirst=True, 
        errors='coerce' # Se houver algo que não seja data, ele vira "NaT" em vez de quebrar o código
    ).dt.date
    
    return df

try:
    df_base = load_data()

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("🗓️ Filtro de Período")
    
    # Filtro de data que já inicia no dia de hoje
    data_selecionada = st.sidebar.date_input(
        "Selecione a Data de Recebimento",
        value=hoje_br
    )

    st.sidebar.divider()
    st.sidebar.header("🚚 Logística")
    
    lista_transportadora = st.sidebar.multiselect(
        "Transportadora 3PL", 
        options=df_base['Transportadora 3PL'].unique(),
        default=df_base['Transportadora 3PL'].unique()
    )

    # --- FILTRAGEM DOS DADOS ---
    # Filtra pela data selecionada E pela transportadora
    mask = (df_base['Data Recebimento'] == data_selecionada) & \
           (df_base['Transportadora 3PL'].isin(lista_transportadora))
    
    df_filtrado = df_base[mask]

    # --- HEADER ---
    col_logo, col_titulo = st.columns([1, 4])
    with col_logo:
        st.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR_xN...", width=150)
    with col_titulo:
        st.title(f"On-holds - LAM 02 Manaus")
        # Mostra o horário de Brasília atualizado
        agora_br = datetime.now(fuso_br).strftime('%H:%M:%S')
        st.info(f"🕒 Horário Brasília: {agora_br} | Visualizando: {data_selecionada.strftime('%d/%m/%Y')}")

    # --- KPIs ---
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Qtd Insucessos (Dia)", len(df_filtrado))
    with c2:
        st.metric("Drivers Ativos", df_filtrado['Driver ID'].nunique())
    with c3:
        if not df_filtrado.empty:
            motivo_top = df_filtrado['Motivo do APP'].mode()[0]
        else:
            motivo_top = "Sem dados"
        st.metric("Motivo Principal", motivo_top)

    st.divider()

    # --- GRÁFICOS ---
    if df_filtrado.empty:
        st.warning(f"Não foram encontrados dados para o dia {data_selecionada.strftime('%d/%m/%Y')}.")
    else:
        g1, g2 = st.columns(2)

        with g1:
            st.subheader("Top 10 insucessos por motorista")
            fig_donut = px.pie(
                df_filtrado, 
                names='Motorista', 
                hole=0.6,
                color_discrete_sequence=px.colors.qualitative.T10
            )
            st.plotly_chart(fig_donut, use_container_width=True)

        with g2:
            st.subheader("Insucessos por Bairro")
            bairros = df_filtrado['Bairro'].value_counts().reset_index()
            fig_bar = px.bar(
                bairros, 
                x='Bairro', 
                y='count', 
                text_auto=True,
                color_discrete_sequence=['#E65100'] # Laranja SPX
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        # --- TABELA ---
        st.subheader("Detalhamento dos Dados")
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Erro: {e}")

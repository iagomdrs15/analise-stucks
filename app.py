import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from streamlit_autorefresh import st_autorefresh

# 1. Configuração da Página (Estilo Web App)
st.set_page_config(
    page_title="Dashboard SPX Express - Manaus",
    page_icon="📦",
    layout="wide"
)

# 2. Atualização Automática (A cada 2 minutos = 120.000 ms)
# Isso faz o script rodar novamente e disparar a atualização dos dados
st_autorefresh(interval=120000, key="auto_refresh_dashboard")

# 3. Estilização CSS para aproximar ao visual da imagem (Opcional)
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 4. Conexão com Google Sheets
def load_data():
    # Substitua pelo link real da sua planilha
    url = "https://docs.google.com/spreadsheets/d/SEU_ID_AQUI/edit#gid=0"
    
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # ttl=120 garante que o cache expire em 2 minutos, forçando a leitura de novos dados
    df = conn.read(spreadsheet=url, ttl=120)
    
    # Garantir que os nomes das colunas não tenham espaços extras
    df.columns = df.columns.str.strip()
    return df

# Tentativa de carregamento
try:
    df = load_data()

    # --- HEADER ---
    col_logo, col_titulo = st.columns([1, 4])
    with col_logo:
        st.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR_xN...", width=150) # Link fictício da logo SPX
    with col_titulo:
        st.title("Recebimento de On-holds - LAM 02 Manaus")
        st.info(f"🕒 Atualizado automaticamente em: {pd.Timestamp.now().strftime('%H:%M:%S')}")

    # --- FILTROS ---
    st.sidebar.header("Painel de Controle")
    lista_transportadora = st.sidebar.multiselect(
        "Transportadora 3PL", 
        options=df['Transportadora 3PL'].unique(),
        default=df['Transportadora 3PL'].unique()
    )

    # Filtragem dos dados
    mask = (df['Transportadora 3PL'].isin(lista_transportadora))
    df_filtrado = df[mask]

    # --- KPIs (Cards do Topo) ---
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Qtd Insucessos", len(df_filtrado))
    with c2:
        st.metric("Drivers", df_filtrado['Driver ID'].nunique())
    with c3:
        # Exemplo de cálculo: Motivos mais comuns
        motivo_top = df_filtrado['Motivo do APP'].mode()[0] if not df_filtrado.empty else "N/A"
        st.metric("Motivo Principal", motivo_top)

    st.divider()

    # --- GRÁFICOS (MEIO) ---
    g1, g2 = st.columns(2)

    with g1:
        st.subheader("Top 10 insucessos por motorista")
        # Gráfico de Rosca (Donut)
        fig_donut = px.pie(
            df_filtrado, 
            names='Motorista', 
            hole=0.6,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with g2:
        st.subheader("Insucessos por Bairro")
        # Gráfico de Barras / Linhas conforme sua imagem
        bairros = df_filtrado['Bairro'].value_counts().reset_index()
        fig_bar = px.bar(
            bairros, 
            x='Bairro', 
            y='count', 
            text_auto=True,
            color_discrete_sequence=['#ef4444'] # Vermelho SPX
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- TABELA DETALHADA ---
    st.subheader("Base de Dados em Tempo Real")
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Erro ao conectar com a planilha: {e}")
    st.info("Certifique-se de que a planilha está compartilhada como 'Qualquer pessoa com o link' ou configurada corretamente no secrets.")

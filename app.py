import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
import pytz

# 1. Configuração da Página
st.set_page_config(page_title="SPX Express - Manaus", page_icon="📊", layout="wide")

# Timezone e Atualização
fuso_br = pytz.timezone('America/Sao_Paulo')
hoje_br = datetime.now(fuso_br).date()
st_autorefresh(interval=120000, key="global_refresh")

# 2. Carga de Dados
@st.cache_data(ttl=120)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1nZV5z9bPoBsi7Xi4PA_WMMQcry7eX1ljGA1c9iLVFW8/edit#gid=0"
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, ttl=120)
    df.columns = df.columns.str.strip()
    df['Data Recebimento'] = pd.to_datetime(df['Data Recebimento'], dayfirst=True, errors='coerce').dt.date
    return df

try:
    df_base = load_data()

    # --- SIDEBAR: MENU DE NAVEGAÇÃO ---
    st.sidebar.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR_xN...", width=150) # Logo SPX
    st.sidebar.title("Navegação")
    aba_selecionada = st.sidebar.radio("Selecione o Módulo:", ["🚫 Gestão de On-holds", "📈 Produtividade"])

    st.sidebar.divider()

    # --- SIDEBAR: FILTROS GLOBAIS ---
    st.sidebar.header("🗓️ Filtros")
    sete_dias = hoje_br - timedelta(days=7)
    range_datas = st.sidebar.date_input("Intervalo", value=(sete_dias, hoje_br), max_value=hoje_br)
    
    lista_3pl = st.sidebar.multiselect("Transportadora", options=df_base['Transportadora 3PL'].unique(), default=df_base['Transportadora 3PL'].unique())

    # Lógica de Filtro Comum
    if len(range_datas) == 2:
        d_ini, d_fim = range_datas
        mask = (df_base['Data Recebimento'] >= d_ini) & (df_base['Data Recebimento'] <= d_fim) & (df_base['Transportadora 3PL'].isin(lista_3pl))
        df_f = df_base[mask]
    else:
        df_f = df_base.copy() # Mostra tudo enquanto seleciona

    # ==========================================
    # MÓDULO: ON HOLD
    # ==========================================
    if aba_selecionada == "🚫 Gestão de On-holds":
        st.title("🚫 Monitoramento de On-holds")
        st.caption(f"🕒 Horário Brasília: {datetime.now(fuso_br).strftime('%H:%M:%S')}")

        # KPIs Rápidos
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Insucessos", len(df_f))
        c2.metric("Bairros Afetados", df_f['Bairro'].nunique())
        c3.metric("Drivers Impactados", df_f['Driver ID'].nunique())

        st.divider()
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.subheader("Maiores Ofensores (Motoristas)")
            st.plotly_chart(px.bar(df_f['Motorista'].value_counts().head(10).reset_index(), x='count', y='Motorista', orientation='h', text_auto=True, color_continuous_scale='Reds', color='count'), use_container_width=True)
        with col_g2:
            st.subheader("Motivos das Ocorrências")
            st.plotly_chart(px.pie(df_f['Motivo do APP'].value_counts().reset_index(), values='count', names='Motivo do APP', hole=0.4), use_container_width=True)

    # ==========================================
    # MÓDULO: PRODUTIVIDADE
    # ==========================================
    elif aba_selecionada == "📈 Produtividade":
        st.title("📈 Análise de Produtividade")
        
        p1, p2 = st.columns(2)
        with p1:
            st.subheader("Volume por Transportadora")
            st.plotly_chart(px.bar(df_f['Transportadora 3PL'].value_counts().reset_index(), x='Transportadora 3PL', y='count', text_auto=True, color='Transportadora 3PL'), use_container_width=True)
        with p2:
            st.subheader("Ranking de Atividade")
            st.plotly_chart(px.bar(df_f['Motorista'].value_counts().head(10).reset_index(), x='Motorista', y='count', text_auto=True), use_container_width=True)

        st.subheader("Histórico de Registros")
        st.dataframe(df_f, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Erro ao carregar dashboard: {e}")

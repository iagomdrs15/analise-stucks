import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
import pytz

# 1. Configuração da Página
st.set_page_config(
    page_title="Gestão SPX - Manaus",
    page_icon="📊",
    layout="wide"
)

# Timezone Brasília
fuso_br = pytz.timezone('America/Sao_Paulo')
hoje_br = datetime.now(fuso_br).date()

# Atualização Automática (2 min)
st_autorefresh(interval=120000, key="auto_refresh_dashboard")

# 2. Conexão e Carga de Dados
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1nZV5z9bPoBsi7Xi4PA_WMMQcry7eX1ljGA1c9iLVFW8/edit#gid=0"
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, ttl=120)
    df.columns = df.columns.str.strip()
    
    # Tratamento de Data
    df['Data Recebimento'] = pd.to_datetime(
        df['Data Recebimento'], 
        dayfirst=True, 
        errors='coerce'
    ).dt.date
    return df

try:
    df_base = load_data()

    # --- BARRA LATERAL (Filtros Globais) ---
    st.sidebar.header("🗓️ Filtro de Período")
    sete_dias_atras = hoje_br - timedelta(days=7)
    range_datas = st.sidebar.date_input("Intervalo", value=(sete_dias_atras, hoje_br), max_value=hoje_br)

    st.sidebar.divider()
    st.sidebar.header("🚚 Filtros de Operação")
    lista_3pl = st.sidebar.multiselect("Transportadora 3PL", options=df_base['Transportadora 3PL'].unique(), default=df_base['Transportadora 3PL'].unique())

    # Lógica de Filtro Temporal
    if len(range_datas) == 2:
        d_ini, d_fim = range_datas
        mask = (df_base['Data Recebimento'] >= d_ini) & (df_base['Data Recebimento'] <= d_fim) & (df_base['Transportadora 3PL'].isin(lista_3pl))
        df_f = df_base[mask]
        texto_p = f"{d_ini.strftime('%d/%m/%Y')} - {d_fim.strftime('%d/%m/%Y')}"
    else:
        df_f = df_base[df_base['Transportadora 3PL'].isin(lista_3pl)]
        texto_p = "Selecione o intervalo completo"

    # --- HEADER PRINCIPAL ---
    st.title("📊 Painel de Operações | SPX Manaus")
    agora = datetime.now(fuso_br).strftime('%H:%M:%S')
    st.caption(f"🕒 Atualizado: {agora} | Período: {texto_p}")

    # --- CRIAÇÃO DAS ABAS ---
    tab_onhold, tab_prod = st.tabs(["🚫 On Hold", "📈 Produtividade"])

    # ==========================================
    # ABA 1: ON HOLD
    # ==========================================
    with tab_onhold:
        if df_f.empty:
            st.warning("Sem dados para o período.")
        else:
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("Total On Holds", len(df_f))
            with c2: 
                top_motivo = df_f['Motivo do APP'].mode()[0] if not df_f.empty else "N/A"
                st.metric("Gargalo Principal", top_motivo)
            with c3: st.metric("Bairros com Problemas", df_f['Bairro'].nunique())

            st.divider()
            g1, g2 = st.columns(2)
            with g1:
                st.subheader("Maiores Ofensores (Motoristas)")
                ofensores = df_f['Motorista'].value_counts().head(10).reset_index()
                st.plotly_chart(px.bar(ofensores, x='count', y='Motorista', orientation='h', text_auto=True, color='count', color_continuous_scale='Reds'), use_container_width=True)
            with g2:
                st.subheader("Distribuição por Motivo")
                st.plotly_chart(px.pie(df_f['Motivo do APP'].value_counts().reset_index(), values='count', names='Motivo do APP', hole=0.4), use_container_width=True)

    # ==========================================
    # ABA 2: PRODUTIVIDADE
    # ==========================================
    with tab_prod:
        if df_f.empty:
            st.warning("Sem dados para o período.")
        else:
            st.subheader("Performance Geral da Operação")
            
            # KPIs de Produtividade
            p1, p2, p3 = st.columns(3)
            with p1:
                total_pedidos = len(df_f) # Aqui você pode ajustar se tiver uma coluna de total geral
                st.metric("Volume Processado", total_pedidos)
            with p2:
                st.metric("Média Pedidos/Dia", round(len(df_f) / ((d_fim - d_ini).days + 1), 1))
            with p3:
                st.metric("Drivers Ativos", df_f['Driver ID'].nunique())

            st.divider()
            
            # Gráfico de Volume por Transportadora
            st.subheader("Volume por Transportadora 3PL")
            transp_vol = df_f['Transportadora 3PL'].value_counts().reset_index()
            fig_transp = px.bar(transp_vol, x='Transportadora 3PL', y='count', color='Transportadora 3PL', text_auto=True, title="Total de Atendimentos por Parceiro")
            st.plotly_chart(fig_transp, use_container_width=True)

            # Ranking de Motoristas mais produtivos (baseado em registros)
            st.subheader("Ranking de Atividade por Motorista")
            rank_mot = df_f['Motorista'].value_counts().head(15).reset_index()
            fig_rank = px.bar(rank_mot, x='Motorista', y='count', text_auto=True, color_discrete_sequence=['#1A237E'])
            st.plotly_chart(fig_rank, use_container_width=True)

    # --- TABELA GLOBAL (FORA DAS ABAS OU DENTRO DE UMA SE EXISTIR) ---
    with st.expander("🔍 Visualizar Base de Dados Completa"):
        st.dataframe(df_f, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Erro Crítico: {e}")

import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
import pytz

# 1. Configuração da Página
st.set_page_config(page_title="SPX Express - Manaus", page_icon="📊", layout="wide")

# Timezone e Atualização (2 min)
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
    
    # Tratamento de Data Brasileira
    df['Data Recebimento'] = pd.to_datetime(
        df['Data Recebimento'], 
        dayfirst=True, 
        errors='coerce'
    ).dt.date
    return df

try:
    df_base = load_data()

    # --- NAVEGAÇÃO POR BOTÕES NA SIDEBAR ---
    if 'segmento' not in st.session_state:
        st.session_state.segmento = "On Hold"

    st.sidebar.title("🎮 Painel de Controle")
    
    # Estilização dos botões para parecerem ativos
    col_btn1, col_btn2 = st.sidebar.columns(2)
    if st.sidebar.button("🚫 On Hold", use_container_width=True):
        st.session_state.segmento = "On Hold"
    
    if st.sidebar.button("📈 Produtividade", use_container_width=True):
        st.session_state.segmento = "Produtividade"

    st.sidebar.divider()

    # --- FILTROS GLOBAIS ---
    st.sidebar.header("🗓️ Filtros de Data")
    sete_dias = hoje_br - timedelta(days=7)
    range_datas = st.sidebar.date_input("Intervalo de Análise", value=(sete_dias, hoje_br), max_value=hoje_br)
    
    st.sidebar.header("🚚 Filtros Operacionais")
    lista_3pl = st.sidebar.multiselect(
        "Transportadora 3PL", 
        options=df_base['Transportadora 3PL'].unique(), 
        default=df_base['Transportadora 3PL'].unique()
    )

    # Lógica de Filtro por Data e Transportadora
    if len(range_datas) == 2:
        d_ini, d_fim = range_datas
        mask = (df_base['Data Recebimento'] >= d_ini) & \
               (df_base['Data Recebimento'] <= d_fim) & \
               (df_base['Transportadora 3PL'].isin(lista_3pl))
        df_f = df_base[mask]
        texto_p = f"{d_ini.strftime('%d/%m/%Y')} até {d_fim.strftime('%d/%m/%Y')}"
    else:
        df_f = df_base[df_base['Transportadora 3PL'].isin(lista_3pl)]
        texto_p = "Selecione a data final"

    # ==========================================
    # MÓDULO: ON HOLD (RESTAURADO)
    # ==========================================
    if st.session_state.segmento == "On Hold":
        st.title("🚫 Gestão de On-holds | LAM 02")
        st.info(f"🕒 Atualização: {datetime.now(fuso_br).strftime('%H:%M:%S')} | Período: {texto_p}")

        if df_f.empty:
            st.warning("Nenhum registro encontrado para este filtro.")
        else:
            # Métricas On Hold
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                ofensores = df_f['Motorista'].value_counts()
                st.metric("Top Ofensor", f"{ofensores.index[0]}", f"{ofensores.iloc[0]} ocorrências", delta_color="inverse")
            with c2: st.metric("Total Insucessos", len(df_f))
            with c3: st.metric("Drivers Impactados", df_f['Driver ID'].nunique())
            with c4: st.metric("Bairros Afetados", df_f['Bairro'].nunique())

            st.divider()
            
            # Gráficos On Hold
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.subheader("🏆 Maiores Ofensores (Motoristas)")
                top_df = df_f['Motorista'].value_counts().head(10).reset_index()
                fig_of = px.bar(top_df, x='count', y='Motorista', orientation='h', text_auto=True, color='count', color_continuous_scale='Reds')
                fig_of.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_of, use_container_width=True)
            
            with col_g2:
                st.subheader("🚨 Motivos das Ocorrências")
                fig_pie = px.pie(df_f['Motivo do APP'].value_counts().reset_index(), values='count', names='Motivo do APP', hole=0.4, color_discrete_sequence=px.colors.qualitative.Bold)
                st.plotly_chart(fig_pie, use_container_width=True)

            st.subheader("📈 Evolução dos Insucessos")
            evolucao = df_f['Data Recebimento'].value_counts().reset_index().sort_values('Data Recebimento')
            st.plotly_chart(px.line(evolucao, x='Data Recebimento', y='count', markers=True, color_discrete_sequence=['#1A237E']), use_container_width=True)

            with st.expander("🔍 Detalhamento da Base"):
                st.dataframe(df_f, use_container_width=True, hide_index=True)

    # ==========================================
    # MÓDULO: PRODUTIVIDADE (EM BRANCO)
    # ==========================================
    elif st.session_state.segmento == "Produtividade":
        st.title("📈 Módulo de Produtividade")
        st.warning("Aguardando definições de métricas de performance para este módulo.")
        st.write("---")
        st.write("Exemplos de métricas futuras: Taxa de entrega, volume por hora, rankings de performance.")

except Exception as e:
    st.error(f"Erro no sistema: {e}")

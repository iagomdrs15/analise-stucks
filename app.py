import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
import pytz

# 1. Configuração da Página
st.set_page_config(
    page_title="Monitoramento SPX - Manaus",
    page_icon="📊",
    layout="wide"
)

# Timezone Brasília
fuso_br = pytz.timezone('America/Sao_Paulo')
hoje_br = datetime.now(fuso_br).date()

# Atualização Automática (2 min)
st_autorefresh(interval=120000, key="auto_refresh_dashboard")

# 4. Conexão e Carga de Dados
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1nZV5z9bPoBsi7Xi4PA_WMMQcry7eX1ljGA1c9iLVFW8/edit#gid=0"
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, ttl=120)
    
    df.columns = df.columns.str.strip()
    
    # Correção Robusta de Data
    df['Data Recebimento'] = pd.to_datetime(
        df['Data Recebimento'], 
        dayfirst=True, 
        errors='coerce'
    ).dt.date
    
    return df

try:
    df_base = load_data()

    # --- BARRA LATERAL ---
    st.sidebar.header("🗓️ Filtro de Período")
    
    # CONFIGURAÇÃO DE RANGE: Inicia com os últimos 7 dias até hoje
    sete_dias_atras = hoje_br - timedelta(days=7)
    
    range_datas = st.sidebar.date_input(
        "Selecione o Intervalo",
        value=(sete_dias_atras, hoje_br),
        max_value=hoje_br
    )

    st.sidebar.divider()
    st.sidebar.header("🚚 Filtros de Operação")
    
    lista_transportadora = st.sidebar.multiselect(
        "Transportadora 3PL", 
        options=df_base['Transportadora 3PL'].unique(),
        default=df_base['Transportadora 3PL'].unique()
    )

    # --- LÓGICA DE FILTRAGEM POR RANGE ---
    if len(range_datas) == 2:
        data_inicio, data_fim = range_datas
        mask = (df_base['Data Recebimento'] >= data_inicio) & \
               (df_base['Data Recebimento'] <= data_fim) & \
               (df_base['Transportadora 3PL'].isin(lista_transportadora))
        texto_periodo = f"de {data_inicio.strftime('%d/%m/%Y')} até {data_fim.strftime('%d/%m/%Y')}"
    else:
        # Enquanto o usuário não seleciona a segunda data do range, não filtra por data
        mask = (df_base['Transportadora 3PL'].isin(lista_transportadora))
        texto_periodo = "Selecione a data final no calendário"

    df_filtrado = df_base[mask]

    # --- HEADER ---
    st.title("📊 Gestão de On-holds | LAM 02 Manaus")
    agora_br = datetime.now(fuso_br).strftime('%H:%M:%S')
    st.info(f"🕒 Atualização automática (2min) | Brasília: {agora_br} | Período: {texto_periodo}")

    # --- MÉTRICAS (KPIs) ---
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        if not df_filtrado.empty:
            ofensores = df_filtrado['Motorista'].value_counts()
            top_motorista = ofensores.index[0]
            top_valor = ofensores.iloc[0]
            st.metric("Líder de Insucessos", f"{top_motorista}", f"{top_valor} total", delta_color="inverse")
        else:
            st.metric("Líder de Insucessos", "N/A")

    with c2:
        st.metric("Total de Insucessos", len(df_filtrado))
    with c3:
        st.metric("Drivers Únicos no Período", df_filtrado['Driver ID'].nunique())
    with c4:
        st.metric("Bairros Atendidos", df_filtrado['Bairro'].nunique())

    st.divider()

    if df_filtrado.empty:
        st.warning("Nenhum dado encontrado para este intervalo.")
    elif len(range_datas) < 2:
        st.info("Por favor, selecione a data final no calendário lateral para completar o intervalo.")
    else:
        # --- GRÁFICOS ---
        g1, g2 = st.columns(2)

        with g1:
            st.subheader(f"🏆 Maiores Ofensores no Período")
            ofensores_df = df_filtrado['Motorista'].value_counts().head(10).reset_index()
            fig_ofensores = px.bar(
                ofensores_df, 
                x='count', 
                y='Motorista', 
                orientation='h',
                text_auto=True,
                color='count',
                color_continuous_scale='Reds'
            )
            fig_ofensores.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_ofensores, use_container_width=True)

        with g2:
            st.subheader("🚨 Ocorrências por Motivo")
            motivos_df = df_filtrado['Motivo do APP'].value_counts().reset_index()
            fig_motivos = px.pie(
                motivos_df, 
                values='count', 
                names='Motivo do APP', 
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            st.plotly_chart(fig_motivos, use_container_width=True)

        # Gráfico de evolução temporal (Novo, útil para ranges)
        st.subheader("📈 Evolução Diária de Insucessos")
        evolucao_df = df_filtrado['Data Recebimento'].value_counts().reset_index().sort_values('Data Recebimento')
        fig_evolucao = px.line(
            evolucao_df, 
            x='Data Recebimento', 
            y='count', 
            markers=True,
            color_discrete_sequence=['#1A237E']
        )
        st.plotly_chart(fig_evolucao, use_container_width=True)

        # --- TABELA ---
        st.subheader("📄 Lista Detalhada")
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Erro Crítico: {e}")

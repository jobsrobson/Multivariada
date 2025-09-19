import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# ==============================================
# Configuração inicial
# ==============================================
st.set_page_config(
    page_title="EDA Acidentes RIDE-DF 2024",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================
# Carregar dados
# ==============================================
@st.cache_data
def load_data(path):
    df = pd.read_csv(path)

    # Conversões
    if "data_inversa" in df.columns:
        df["data_inversa"] = pd.to_datetime(df["data_inversa"], errors="coerce")
    if "horario" in df.columns:
        h = pd.to_datetime(df["horario"], errors="coerce", format="%H:%M:%S")
        if h.isna().all():
            h = pd.to_datetime(df["horario"], errors="coerce", format="%H:%M")
        df["hora"] = h.dt.hour

    for c in ["latitude", "longitude"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # === Ajuste solicitado ===
    cols_int = ["ilesos", "feridos_leves", "feridos_graves", "mortos"]
    for col in cols_int:
        if col not in df.columns:
            df[col] = 0
        df[col] = df[col].fillna(0).astype(int)

    df["total_vitimas"] = (
        df[["feridos_leves", "feridos_graves", "mortos"]].sum(axis=1)
    ).astype(int)

    df["tem_vitimas"] = np.where(df["total_vitimas"] > 0, 1, 0)

    return df

df = load_data("data/acidentes_ride.csv")


# ==============================================
# Barra lateral
# ==============================================
st.sidebar.header("Análise Exploratória de Acidentes de Trânsito na RIDE-DF (2024)")
st.sidebar.markdown("Fonte dos Dados: PRF")
section = st.sidebar.radio(
    "Escolha a seção:",
    [
        "Visão Geral",
        "Distribuições",
        "Tempo",
        "Severidade",
        "Geografia",
        "Tabelas"
    ]
)

# ==============================================
# 1) Visão Geral
# ==============================================
if section == "Visão Geral":

    st.subheader("Visão Geral dos Acidentes de Trânsito")
    
    st.markdown("<br>", unsafe_allow_html=True)

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💥 Total de registros", f"{df.shape[0]:,}".replace(",", "."))
    col2.metric("🗺️ Municípios da RIDE", df["municipio"].nunique())
    col3.metric("🚑 Total de vítimas", int(df["total_vitimas"].sum()))
    col4.metric("📉 Vítimas por acidente", round(df["total_vitimas"].sum() / df["id"].nunique(), 2))

    st.divider()
    
    # === Gráfico: Top 10 municípios ===
    if "municipio" in df.columns:
        top_mun = df["municipio"].value_counts().reset_index().head(10)
        top_mun.columns = ["Município", "Acidentes"]
        st.write("###### 🏙️ Top 10 Municípios com Mais Acidentes")
        fig = px.bar(top_mun, x="Município", y="Acidentes",
                     text="Acidentes")
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    
    st.divider()

    # === Gráfico: Evolução mensal ===
    if "data_inversa" in df.columns:
        temp = df["data_inversa"].dt.to_period("M").value_counts().sort_index().reset_index()
        temp.columns = ["Mês","Acidentes"]
        temp["Mês"] = temp["Mês"].astype(str)
        st.write("###### 📅 Evolução Mensal de Acidentes")
        fig = px.line(temp, x="Mês", y="Acidentes", markers=True)
        st.plotly_chart(fig, use_container_width=True)

    
    st.divider()

    # === Gráfico: Com vítimas x Sem vítimas ===
    if "tem_vitimas" in df.columns:
            vc = df["tem_vitimas"].map({1: "Com vítimas", 0: "Sem vítimas"}).value_counts().reset_index()
            vc.columns = ["Categoria", "Contagem"]
            st.write("###### ⚠️ Acidentes com e sem vítimas")
            fig = px.bar(vc, x="Categoria", y="Contagem", text="Contagem")
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)
    
    st.divider()

    # === Tabelas Resumo ===
    st.write("###### 📊 Resumo por Município")
    municipios_analisados = df.groupby("municipio").agg(
        Acidentes=("id","count"),
        Vítimas=("total_vitimas","sum"),
        Mortos=("mortos","sum")
    ).reset_index().sort_values("Acidentes", ascending=False)
    st.dataframe(municipios_analisados, use_container_width=True, hide_index=True)
    

# ==============================================
# 2) Distribuições
# ==============================================
elif section == "Distribuições":
    st.subheader("📊 Distribuições principais")

    # Variável categórica escolhida
    opt = st.selectbox("Escolha a variável categórica:", [
        "municipio", "causa_principal", "causa_acidente",
        "tipo_acidente", "condicao_metereologica",
        "tipo_pista", "tracado_via", "uso_solo", "tipo_veiculo", "sexo"
    ])

    if opt in df.columns:
        vc = df[opt].astype("string").fillna("NA").value_counts().reset_index()
        vc.columns = [opt, "contagem"]
        st.write(f"###### Distribuição de {opt}")
        fig = px.bar(vc.head(20), x=opt, y="contagem")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ===== Idade =====
    if "idade" in df.columns:
        df_idade = pd.to_numeric(df["idade"], errors="coerce")
        df_idade = df_idade[(df_idade >= 0) & (df_idade <= 100)]
        st.write("###### Distribuição de Idade (0 a 100 anos)")
        fig = px.histogram(df_idade, x=df_idade, nbins=25)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ===== Ano de fabricação do veículo =====
    if "ano_fabricacao_veiculo" in df.columns:
        ano_atual = pd.Timestamp.today().year
        df_ano = pd.to_numeric(df["ano_fabricacao_veiculo"], errors="coerce")
        df_ano = df_ano[(df_ano >= 1970) & (df_ano <= ano_atual)]
        st.write("###### Ano de fabricação dos veículos (1970 até atual)")
        fig = px.histogram(df_ano, x=df_ano, nbins=30)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ===== Top tipos de veículos =====
    if "tipo_veiculo" in df.columns:
        vc = df["tipo_veiculo"].value_counts().reset_index().head(15)
        vc.columns = ["Tipo de veículo", "Contagem"]
        st.write("###### Top 15 tipos de veículos envolvidos")
        fig = px.bar(vc, x="Tipo de veículo", y="Contagem")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ===== Top tipos de acidente =====
    if "tipo_acidente" in df.columns:
        vc = df["tipo_acidente"].value_counts().reset_index().head(10)
        vc.columns = ["Tipo de acidente", "Contagem"]
        st.write("###### Top 10 tipos de acidente")
        fig = px.bar(vc, x="Tipo de acidente", y="Contagem")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ===== Condições meteorológicas =====
    if "condicao_metereologica" in df.columns:
        vc = df["condicao_metereologica"].value_counts().reset_index()
        vc.columns = ["Condição meteorológica", "Contagem"]
        st.write("###### Distribuição das condições meteorológicas")
        fig = px.pie(vc, names="Condição meteorológica", values="Contagem")
        st.plotly_chart(fig, use_container_width=True)




# ==============================================
# 3) Tempo
# ==============================================
elif section == "Tempo":
    st.subheader("Distribuições temporais")

    if "dia_semana" in df.columns:
        vc = df["dia_semana"].str.lower().value_counts().reset_index()
        vc.columns = ["dia_semana","contagem"]
        fig = px.bar(vc, x="dia_semana", y="contagem", title="Distribuição por dia da semana")
        st.plotly_chart(fig, use_container_width=True)

    if "hora" in df.columns:
        fig = px.histogram(df, x="hora", nbins=24, title="Distribuição por hora do dia")
        st.plotly_chart(fig, use_container_width=True)

    if "data_inversa" in df.columns:
        temp = (
            df["data_inversa"]
            .dt.to_period("M")
            .value_counts()
            .sort_index()
            .reset_index()
        )
        temp.columns = ["mes","acidentes"]
        # 🔧 conversão necessária para string
        temp["mes"] = temp["mes"].astype(str)

        fig = px.line(temp, x="mes", y="acidentes", markers=True,
                      title="Série temporal - Acidentes por mês")
        st.plotly_chart(fig, use_container_width=True)

# ==============================================
# 4) Severidade
# ==============================================
elif section == "Severidade":
    st.subheader("⚠️ Severidade dos acidentes")

    # --- preparar dados agregados ---
    def preparar_agregado(df):
        if "id" in df.columns:
            agg = df.groupby("id").agg(
                ilesos=("ilesos","sum"),
                feridos_leves=("feridos_leves","sum"),
                feridos_graves=("feridos_graves","sum"),
                mortos=("mortos","sum"),
                total_vitimas=("total_vitimas","sum")
            ).reset_index()
            return agg
        return df

    df_agregado = preparar_agregado(df)

    # --- gráfico com/sem vítimas ---
    if "total_vitimas" in df_agregado.columns:
        df_agregado["tem_vitimas"] = np.where(df_agregado["total_vitimas"] > 0, "Com vítimas", "Sem vítimas")
        vc = df_agregado["tem_vitimas"].value_counts().reset_index()
        vc.columns = ["Categoria", "Contagem"]
        fig = px.bar(vc, x="Categoria", y="Contagem", title="Proporção de acidentes com/sem vítimas")
        st.plotly_chart(fig, use_container_width=True)

    # --- histogramas por tipo de gravidade ---
    for var in ["ilesos","feridos_leves","feridos_graves","mortos","total_vitimas"]:
        if var in df_agregado.columns:
            fig = px.histogram(
                df_agregado, x=var, nbins=30,
                title=f"Distribuição de {var} por acidente"
            )
            st.plotly_chart(fig, use_container_width=True)

    # --- tabela resumo ---
    resumo = df_agregado[["ilesos","feridos_leves","feridos_graves","mortos","total_vitimas"]].sum().reset_index()
    resumo.columns = ["Categoria", "Total"]
    st.write("### Totais de vítimas na base (2024)")
    st.dataframe(resumo, use_container_width=True)


# ==============================================
# 5) Geografia
# ==============================================
elif section == "Geografia":
    st.subheader("🗺️ Visualização geográfica")

    if {"latitude","longitude"}.issubset(df.columns):
        st.map(df[["latitude","longitude"]].dropna().sample(min(2000, len(df))))

# ==============================================
# 6) Tabelas
# ==============================================
elif section == "Tabelas":
    st.subheader("📑 Tabelas agregadas")

    if "municipio" in df.columns:
        agg = df.groupby("municipio").agg(
            acidentes=("id","count"),
            com_vitimas=("tem_vitimas","sum"),
            mortos=("mortos","sum")
        ).reset_index().sort_values("acidentes", ascending=False)

        st.write("### Acidentes por município")
        st.dataframe(agg, use_container_width=True)

    if "tipo_acidente" in df.columns:
        vc = df["tipo_acidente"].value_counts().reset_index()
        vc.columns = ["Tipo de acidente","Contagem"]
        st.write("### Tipo de acidente")
        st.dataframe(vc, use_container_width=True)

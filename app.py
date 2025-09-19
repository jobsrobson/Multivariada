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

    col1, col2 = st.columns(2)
    with col1:
        # === Gráfico: Evolução mensal ===
        if "data_inversa" in df.columns:
            temp = df["data_inversa"].dt.to_period("M").value_counts().sort_index().reset_index()
            temp.columns = ["Mês","Acidentes"]
        temp["Mês"] = temp["Mês"].astype(str)
        st.write("###### 📅 Evolução Mensal de Acidentes")
        fig = px.line(temp, x="Mês", y="Acidentes", markers=True)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # === Gráfico: Com vítimas x Sem vítimas ===
        if "tem_vitimas" in df.columns:
            vc = df["tem_vitimas"].map({1: "Com vítimas", 0: "Sem vítimas"}).value_counts().reset_index()
            vc.columns = ["Categoria", "Contagem"]
            st.write("###### ⚠️ Acidentes com e sem vítimas")
            fig = px.pie(vc, names="Categoria", values="Contagem", hole=0.4)
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
    st.subheader("Distribuições")
    st.markdown("<br>", unsafe_allow_html=True)

    # Variável categórica escolhida
    opt = st.selectbox("Escolha a variável categórica:", [
        "municipio", "causa_principal", "causa_acidente",
        "tipo_acidente", "condicao_metereologica",
        "tipo_pista", "tracado_via", "uso_solo", "tipo_veiculo", "sexo"
    ])

    # Em "sexo", substituir 0 por "Não Informado"
    if opt == "sexo" and "sexo" in df.columns:
        df["sexo"] = df["sexo"].replace({"0": "Não Informado"})


    if opt in df.columns:
        vc = df[opt].astype("string").fillna("NA").value_counts().reset_index()
        vc.columns = [opt, "contagem"]
        st.write(f"###### 📈 Distribuição de {opt}")
        fig = px.bar(vc.head(20), x=opt, y="contagem")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ===== Idade =====
    if "idade" in df.columns:
        df_idade = pd.to_numeric(df["idade"], errors="coerce")
        df_idade = df_idade[(df_idade >= 0) & (df_idade <= 100)]
        st.write("###### 👴 Distribuição de Idade (0 a 100 anos)")
        fig = px.histogram(df_idade, x=df_idade, nbins=25)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ===== Ano de fabricação do veículo =====
    if "ano_fabricacao_veiculo" in df.columns:
        ano_atual = pd.Timestamp.today().year
        df_ano = pd.to_numeric(df["ano_fabricacao_veiculo"], errors="coerce")
        df_ano = df_ano[(df_ano >= 1970) & (df_ano <= ano_atual)]
        st.write("###### 🚗 Ano de fabricação dos veículos (1970 até atual)")
        fig = px.histogram(df_ano, x=df_ano, nbins=30)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ===== Top tipos de veículos =====
    if "tipo_veiculo" in df.columns:
        # Replace 0 por "Não Informado"
        df["tipo_veiculo"] = df["tipo_veiculo"].replace({"0": "Não Informado"})
        df["tipo_veiculo"] = df["tipo_veiculo"].replace({"NA/NA": "Não Informado"})
        vc = df["tipo_veiculo"].value_counts().reset_index().head(15)
        vc.columns = ["Tipo de veículo", "Contagem"]
        st.write("###### 🚙 Top 15 tipos de veículos envolvidos")
        fig = px.bar(vc, x="Tipo de veículo", y="Contagem")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ===== Top marcas de veículos =====
    if "marca" in df.columns:
        # Replace NA/NA por "Não Informado"
        df["marca"] = df["marca"].replace({"NA/NA": "Não Informado"})
        # Replace Não Informado/Não Informado por "Não Informado"
        df["marca"] = df["marca"].replace({"Não Informado/Não Informado": "Não Informado"})
        vc = df["marca"].astype("string").fillna("NA").value_counts().reset_index().head(15)
        vc.columns = ["Marca do veículo", "Contagem"]
        st.write("###### 🚘 Top 15 marcas/modelos de veículos envolvidos")
        fig = px.bar(vc, x="Marca do veículo", y="Contagem")
        st.plotly_chart(fig, use_container_width=True)

    # ===== Top tipos de acidente =====
    if "tipo_acidente" in df.columns:
        vc = df["tipo_acidente"].value_counts().reset_index().head(10)
        vc.columns = ["Tipo de acidente", "Contagem"]
        st.write("###### 🚨 Top 10 tipos de acidente")
        fig = px.bar(vc, x="Tipo de acidente", y="Contagem")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ===== Top causas de acidente =====
    if "causa_acidente" in df.columns:
        vc = df["causa_acidente"].value_counts().reset_index().head(10)
        vc.columns = ["Causa do acidente", "Contagem"]
        st.write("###### ⚠️ Top 10 causas de acidente")
        fig = px.bar(vc, x="Causa do acidente", y="Contagem")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        # ===== Condições meteorológicas =====
        if "condicao_metereologica" in df.columns:
            vc = df["condicao_metereologica"].value_counts().reset_index()
            vc.columns = ["Condição meteorológica", "Contagem"]
            st.write("###### 🌦️ Distribuição das condições meteorológicas")
            fig = px.pie(vc, names="Condição meteorológica", values="Contagem")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # ===== Tipo de pista =====
        if "tipo_pista" in df.columns:
            vc = df["tipo_pista"].value_counts().reset_index()
            vc.columns = ["Tipo de pista", "Contagem"]
            st.write("###### 🛣️ Distribuição dos tipos de pista")
            fig = px.pie(vc, names="Tipo de pista", values="Contagem")
            st.plotly_chart(fig, use_container_width=True)



# ==============================================
# 3) Tempo
# ==============================================
elif section == "Tempo":
    st.subheader("Distribuições Temporais")
    st.markdown("<br>", unsafe_allow_html=True)

    # ===== Dia da semana =====
    if "dia_semana" in df.columns:
        dias_ord = ["segunda-feira","terça-feira","quarta-feira",
                    "quinta-feira","sexta-feira","sábado","domingo"]
        vc = df["dia_semana"].str.lower().value_counts()
        vc = vc.reindex(dias_ord).dropna().reset_index()
        vc.columns = ["dia_semana","contagem"]
        st.write("###### 📅 Acidentes por dia da semana")
        fig = px.bar(vc, x="dia_semana", y="contagem")
    
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ===== Hora do dia =====
    if "hora" in df.columns:
        st.write("###### 🕒 Distribuição de acidentes por hora do dia")
        fig = px.histogram(df, x="hora", nbins=24)
    
        st.plotly_chart(fig, use_container_width=True)

        # vítimas médias por hora
        if "total_vitimas" in df.columns:
            vit_hora = df.groupby("hora")["total_vitimas"].mean().reset_index()
            st.write("###### 💀 Média de vítimas por hora do dia")
            fig = px.line(vit_hora, x="hora", y="total_vitimas", markers=True)
        
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ===== Série temporal mensal =====
    if "data_inversa" in df.columns:
        temp = (
            df["data_inversa"]
            .dt.to_period("M")
            .value_counts()
            .sort_index()
            .reset_index()
        )
        temp.columns = ["mes","acidentes"]
        temp["mes"] = temp["mes"].astype(str)

        st.write("###### 📈 Evolução mensal de acidentes")
        fig = px.line(temp, x="mes", y="acidentes", markers=True)
    
        st.plotly_chart(fig, use_container_width=True)

        # evolução mensal de mortos e feridos
        evol = (
            df.assign(mes=df["data_inversa"].dt.to_period("M").astype(str))
              .groupby("mes")[["feridos_leves","feridos_graves","mortos"]]
              .sum()
              .reset_index()
        )
        st.write("###### 📉 Evolução mensal de feridos e mortos")
        fig = px.line(evol, x="mes", y=["feridos_leves","feridos_graves","mortos"], markers=True)
    
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ===== Heatmap Hora x Dia da semana =====
    if {"hora","dia_semana"}.issubset(df.columns):
        heat = df.groupby([df["dia_semana"].str.lower(), "hora"]).size().reset_index(name="contagem")
        # ordenar dias
        heat["dia_semana"] = pd.Categorical(
            heat["dia_semana"],
            categories=["segunda-feira","terça-feira","quarta-feira",
                        "quinta-feira","sexta-feira","sábado","domingo"],
            ordered=True
        )
        st.write("###### 🆘 Heatmap: acidentes por dia da semana e hora")
        fig = px.density_heatmap(
            heat, x="hora", y="dia_semana", z="contagem", color_continuous_scale="Reds"
        )
    
        st.plotly_chart(fig, use_container_width=True)


# ==============================================
# 4) Severidade
# ==============================================
elif section == "Severidade":
    st.subheader("Severidade dos acidentes")
    st.markdown("<br>", unsafe_allow_html=True)

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

    col1, col2 = st.columns(2)

    with col1:
        # --- gráfico com/sem vítimas ---
        if "total_vitimas" in df_agregado.columns:
            df_agregado["tem_vitimas"] = np.where(
                df_agregado["total_vitimas"] > 0, "Com vítimas", "Sem vítimas"
            )
            vc = df_agregado["tem_vitimas"].value_counts().reset_index()
            vc.columns = ["Categoria", "Acidentes"]

            st.write("###### 💀 Proporção de acidentes com/sem vítimas")
            fig = px.pie(vc, names="Categoria", values="Acidentes", hole=0.4)
            
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # --- histogramas por tipo de gravidade ---
        if "ilesos" in df_agregado.columns:
            st.write("###### 😅 Distribuição de ilesos por acidente")
            fig = px.histogram(df_agregado, x="ilesos", nbins=30)
            st.plotly_chart(fig, use_container_width=True)

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if "feridos_leves" in df_agregado.columns:
            st.write("###### 🤕 Distribuição de feridos leves por acidente")
            fig = px.histogram(df_agregado, x="feridos_leves", nbins=30)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if "feridos_graves" in df_agregado.columns:
            st.write("###### 🚑 Distribuição de feridos graves por acidente")
            fig = px.histogram(df_agregado, x="feridos_graves", nbins=30)
            st.plotly_chart(fig, use_container_width=True)

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if "mortos" in df_agregado.columns:
            st.write("###### 😵 Distribuição de mortos por acidente")
            fig = px.histogram(df_agregado, x="mortos", nbins=30)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if "total_vitimas" in df_agregado.columns:
            st.write("###### ☠️ Distribuição de total de vítimas por acidente")
            fig = px.histogram(df_agregado, x="total_vitimas", nbins=30)
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        # --- boxplots para severidade ---
        st.write("###### 📈 Distribuição de vítimas por acidente (Boxplot)")
        df_melt = df_agregado.melt(
            id_vars="id",
            value_vars=["feridos_leves","feridos_graves","mortos"],
            var_name="Categoria", value_name="Quantidade"
        )
        fig = px.box(df_melt, x="Categoria", y="Quantidade")
        
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # --- gráfico de barras comparativo (totais) ---
        resumo = df_agregado[["ilesos","feridos_leves","feridos_graves","mortos","total_vitimas"]].sum().reset_index()
        resumo.columns = ["Categoria", "Total"]

        st.write("###### 🚨 Totais de vítimas na base (2024)")
        fig = px.bar(resumo, x="Categoria", y="Total", text="Total")
        fig.update_traces(textposition="outside")
    
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        # --- Rodovia mais letal ---

        # Tratar "br" como string
        if "br" in df.columns:
            df["br"] = df["br"].astype("string").fillna("NA")
            # Adiciona um "0" na frente dos números
            df["br"] = df["br"].apply(lambda x: x if not x.isdigit() else f"BR-{int(x):03d}")

            # Agrega o número de mortos por rodovia
            rodovias = df.groupby("br")["mortos"].sum().reset_index()
            rodovias = rodovias[rodovias["br"] != "NA"]
            rodovias = rodovias.sort_values("mortos", ascending=False).head(5)
            st.write("###### 🛣️ Top 5 rodovias com mais mortos")
            fig = px.pie(rodovias, names="br", values="mortos", hole=0.4)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Top causas de acidente com mortos nas rodovias mais letais
        if {"br","causa_acidente","mortos"}.issubset(df.columns):
            top_rodovias = rodovias["br"].head(3).tolist()
            causas = (
                df[df["br"].isin(top_rodovias) & (df["mortos"] > 0)]
                .groupby(["br","causa_acidente"])["mortos"]
                .sum()
                .reset_index()
            )
            causas = causas.sort_values(["br","mortos"], ascending=[True, False])
            causas = causas.groupby("br").head(3).reset_index(drop=True)
            st.write("###### ⚠️ Top 3 causas de acidente com mortos nas rodovias mais letais")
            fig = px.bar(causas, x="causa_acidente", y="mortos", color="br", barmode="group")
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        # Top marcas de veículos envolvidos em acidentes com mortos
        if {"marca","mortos"}.issubset(df.columns):
            # Replace NA/NA por "Não Informado"
            df["marca"] = df["marca"].replace({"NA/NA": "Não Informado"})
            # Replace Não Informado/Não Informado por "Não Informado"
            df["marca"] = df["marca"].replace({"Não Informado/Não Informado": "Não Informado"})
            marcas = (
                df[df["mortos"] > 0]
                .groupby("marca")["mortos"]
                .sum()
                .reset_index()
            )
            marcas = marcas.sort_values("mortos", ascending=False).head(10)
            st.write("###### 🚘 Top 10 marcas de veículos envolvidos em acidentes com mortos")
            fig = px.bar(marcas, x="marca", y="mortos")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Top tipos de veículos envolvidos em acidentes com mortos
        if {"tipo_veiculo","mortos"}.issubset(df.columns):
            # Replace 0 por "Não Informado"
            df["tipo_veiculo"] = df["tipo_veiculo"].replace({"0": "Não Informado"})
            tipos = (
                df[df["mortos"] > 0]
                .groupby("tipo_veiculo")["mortos"]
                .sum()
                .reset_index()
            )
            tipos = tipos.sort_values("mortos", ascending=False).head(10)
            st.write("###### 🚙 Top 10 tipos de veículos envolvidos em acidentes com mortos")
            fig = px.bar(tipos, x="tipo_veiculo", y="mortos")
            st.plotly_chart(fig, use_container_width=True)
                                                     
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        # Top tipos de envolvidos em acidentes com mortos
        if {"tipo_envolvido","mortos"}.issubset(df.columns):
            tipos = (
                df[df["mortos"] > 0]
                .groupby("tipo_envolvido")["mortos"]
                .sum()
                .reset_index()
            )
            tipos = tipos.sort_values("mortos", ascending=False).head(10)
            st.write("###### 💀 Top 10 tipos de envolvidos em acidentes com mortos")
            fig = px.pie(tipos, names="tipo_envolvido", values="mortos", hole=0.4)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Top Faixas Etárias em acidentes com mortos
        if {"idade","mortos"}.issubset(df.columns):
            df_idade = pd.to_numeric(df["idade"], errors="coerce")
            df_idade = df_idade[(df_idade >= 0) & (df_idade <= 100)]
            faixas = (
                df[df["mortos"] > 0]
                .assign(faixa_etaria=pd.cut(df_idade, bins=[0,18,30,45,60,75,100], right=False,
                                           labels=["0-17","18-29","30-44","45-59","60-74","75+"]))
                .groupby("faixa_etaria")["mortos"]
                .sum()
                .reset_index()
            )
            faixas = faixas.sort_values("mortos", ascending=False)
            st.write("###### 👵 Top faixas etárias em acidentes com mortos")
            fig = px.bar(faixas, x="faixa_etaria", y="mortos")
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    col1, col2 = st.columns(2, gap="large")
    with col1:
        # Top idades de veículos envolvidos em acidentes totais
        if {"ano_fabricacao_veiculo","total_vitimas"}.issubset(df.columns):
            ano_atual = pd.Timestamp.today().year
            df_ano = pd.to_numeric(df["ano_fabricacao_veiculo"], errors="coerce")
            df_ano = df_ano[(df_ano >= 1960) & (df_ano <= ano_atual)]
            idades = (
                df.assign(idade_veiculo=ano_atual - df_ano)
                  .groupby("idade_veiculo")["total_vitimas"]
                  .sum()
                  .reset_index()
            )
            idades = idades.sort_values("total_vitimas", ascending=False).head(10)
            st.write("###### 🚗 Idades de veículos envolvidos em acidentes (total de vítimas)")
            fig = px.bar(idades, x="idade_veiculo", y="total_vitimas")
            # Adiciona linha de média
            media = idades["idade_veiculo"].mean()
            fig.add_vline(x=media, line_dash="dash", line_color="red",
                          annotation_text=f"Média: {media:.1f}", annotation_position="top right")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Marca de veículos com maior idade, que se envolveram em acidentes (vítimas graves e mortos)
        if {"marca","ano_fabricacao_veiculo","feridos_graves","mortos"}.issubset(df.columns):
            ano_atual = pd.Timestamp.today().year
            df_ano = pd.to_numeric(df["ano_fabricacao_veiculo"], errors="coerce")
            df_ano = df_ano[(df_ano >= 1960) & (df_ano <= ano_atual)]
            marcas_idade = (
            df[(df["feridos_graves"] > 0) | (df["mortos"] > 0)]
            .assign(idade_veiculo=ano_atual - df_ano)
            .groupby("marca")
            .agg(
                idade_veiculo_media=("idade_veiculo", "mean"),
                acidentes=("id", "count")
            )
            .reset_index()
            )
            marcas_idade = marcas_idade.sort_values("idade_veiculo_media", ascending=False)
            st.write("###### 🚙 Veículos com maior idade, envolvidos em acidentes (vítimas graves e mortos)")
            st.dataframe(marcas_idade, use_container_width=True, hide_index=True)

    # --- tabela resumo ---
    st.dataframe(resumo, use_container_width=True, hide_index=True)
    st.markdown("**Nota:** A soma dos totais pode não coincidir exatamente com o total de vítimas devido a acidentes com múltiplas vítimas.")


# ==============================================
# 5) Geografia
# ==============================================
elif section == "Geografia":
    st.subheader("Visualização Geográfica")
    st.markdown("<br>", unsafe_allow_html=True)

    if {"latitude","longitude"}.issubset(df.columns):

        # Amostragem para não sobrecarregar
        df_geo = df[["latitude","longitude","mortos","total_vitimas"]].dropna()


        # Categorizar severidade
        df_geo["Severidade"] = np.where(
            df_geo["mortos"] > 0, "Com mortos",
            np.where(df_geo["total_vitimas"] > 0, "Com feridos", "Somente danos")
        )

        # Scatter Mapbox
        st.write("###### 🌐 Acidentes georreferenciados (amostra)")
        fig = px.scatter_map(
            df_geo,
            lat="latitude", lon="longitude",
            color="Severidade",
            zoom=7,
            height=600,
            opacity=1,
            color_discrete_map={
                "Somente danos": "blue",
                "Com feridos": "orange",
                "Com mortos": "red"
            }
        )
        fig.update_layout(mapbox_style="open-street-map")
        fig.update_layout(title=None, margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})

        st.divider()

        # Agregação por município
        if "municipio" in df.columns:
            agg = df.groupby("municipio").agg(
                acidentes=("id","count"),
                vitimas=("total_vitimas","sum"),
                mortos=("mortos","sum"),
                latitude=("latitude","mean"),
                longitude=("longitude","mean")
            ).reset_index()

            st.write("###### 🧭 Acidentes agregados por município")
            fig = px.scatter_map(
                agg,
                lat="latitude", lon="longitude",
                size="acidentes",
                color="mortos",
                hover_name="municipio",
                hover_data={"acidentes":True,"vitimas":True,"mortos":True},
                zoom=7,
                height=600,
                color_continuous_scale="Reds"
            )
            fig.update_layout(mapbox_style="open-street-map")
            fig.update_layout(title=None, margin={"r":0,"t":0,"l":0,"b":0})
            st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})


# ==============================================
# 6) Tabelas
# ==============================================
elif section == "Tabelas":
    st.subheader("Tabelas Agregadas")
    st.markdown("<br>", unsafe_allow_html=True)

    # ===== Agregado por município =====
    if "municipio" in df.columns:
        agg = df.groupby("municipio").agg(
            acidentes=("id","count"),
            com_vitimas=("tem_vitimas","sum"),
            feridos_leves=("feridos_leves","sum"),
            feridos_graves=("feridos_graves","sum"),
            mortos=("mortos","sum")
        ).reset_index().sort_values("acidentes", ascending=False)

        agg["% com vítimas"] = (agg["com_vitimas"] / agg["acidentes"] * 100).round(1)

        st.write("###### 🏙️ Acidentes por município")
        st.dataframe(agg, use_container_width=True, hide_index=True)

    st.divider()

    # ===== Agregado por tipo de acidente =====
    if "tipo_acidente" in df.columns:
        vc = df["tipo_acidente"].value_counts().reset_index()
        vc.columns = ["Tipo de acidente","Contagem"]
        vc["Proporção (%)"] = (vc["Contagem"] / vc["Contagem"].sum() * 100).round(1)

        st.write("###### 🚦 Distribuição por tipo de acidente")
        st.dataframe(vc, use_container_width=True, hide_index=True)

    st.divider()

    # ===== Agregado por condição meteorológica =====
    if "condicao_metereologica" in df.columns:
        vc = df["condicao_metereologica"].value_counts().reset_index()
        vc.columns = ["Condição meteorológica","Contagem"]
        vc["Proporção (%)"] = (vc["Contagem"] / vc["Contagem"].sum() * 100).round(1)

        st.write("###### 🌩️ Distribuição por condição meteorológica")
        st.dataframe(vc, use_container_width=True, hide_index=True)

    st.divider()

    # ===== Agregado por tipo de veículo =====
    if "tipo_veiculo" in df.columns:
        vc = df["tipo_veiculo"].value_counts().reset_index().head(15)
        vc.columns = ["Tipo de veículo","Contagem"]
        vc["Proporção (%)"] = (vc["Contagem"] / df["tipo_veiculo"].shape[0] * 100).round(1)

        st.write("###### 🚘 Top 15 tipos de veículos envolvidos")
        st.dataframe(vc, use_container_width=True, hide_index=True)

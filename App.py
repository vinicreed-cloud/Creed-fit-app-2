# app.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
import plotly.express as px

# =========================================================
# CONFIGURAÇÃO INICIAL
# =========================================================

st.set_page_config(
    page_title="Health Tracker",
    page_icon="🏋️",
    layout="centered"
)

# =========================================================
# DADOS FIXOS DO USUÁRIO
# =========================================================

IDADE = 30
ALTURA = 186  # cm
SEXO = "Homem"

# =========================================================
# FUNÇÕES
# =========================================================

def calcular_tmb(peso):
    """
    Fórmula de Mifflin-St Jeor
    Homem:
    TMB = (10 × peso) + (6.25 × altura) − (5 × idade) + 5
    """
    return (10 * peso) + (6.25 * ALTURA) - (5 * IDADE) + 5


def calcular_get(tmb, fator_atividade=1.55):
    """
    GET = TMB x fator atividade
    """
    return tmb * fator_atividade


def meta_emagrecimento(get):
    return get - 500


def meta_agua(peso):
    return peso * 35  # ml


def inicializar_session():
    if "peso_atual" not in st.session_state:
        st.session_state.peso_atual = 107.0

    if "historico_peso" not in st.session_state:
        st.session_state.historico_peso = pd.DataFrame(
            [{
                "Data": datetime.now(),
                "Peso": st.session_state.peso_atual
            }]
        )

    if "alimentos" not in st.session_state:
        st.session_state.alimentos = pd.DataFrame([
            {"Alimento": "Arroz", "Tipo": "g", "Kcal_base": 130, "Kcal_g": 1.30},
            {"Alimento": "Feijão", "Tipo": "g", "Kcal_base": 76, "Kcal_g": 0.76},
            {"Alimento": "Frango", "Tipo": "g", "Kcal_base": 165, "Kcal_g": 1.65},
            {"Alimento": "Ovo", "Tipo": "un", "Kcal_base": 70, "Kcal_g": 70},
            {"Alimento": "Banana", "Tipo": "un", "Kcal_base": 90, "Kcal_g": 90},
        ])

    if "carrinho" not in st.session_state:
        st.session_state.carrinho = []

    if "historico_refeicoes" not in st.session_state:
        st.session_state.historico_refeicoes = pd.DataFrame(
            columns=[
                "Data",
                "Refeicao",
                "Alimento",
                "Quantidade",
                "Calorias"
            ]
        )

    if "historico_exercicios" not in st.session_state:
        st.session_state.historico_exercicios = pd.DataFrame(
            columns=[
                "Data",
                "Atividade",
                "Duracao",
                "Calorias"
            ]
        )


inicializar_session()

# =========================================================
# CÁLCULOS
# =========================================================

peso_atual = st.session_state.peso_atual

TMB = calcular_tmb(peso_atual)
GET = calcular_get(TMB)
META_KCAL = meta_emagrecimento(GET)
META_AGUA = meta_agua(peso_atual)

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("⚙️ Perfil")

novo_peso = st.sidebar.number_input(
    "Peso Atual (kg)",
    min_value=30.0,
    max_value=300.0,
    value=float(st.session_state.peso_atual),
    step=0.1
)

if novo_peso != st.session_state.peso_atual:
    st.session_state.peso_atual = novo_peso

    novo_registro = pd.DataFrame([{
        "Data": datetime.now(),
        "Peso": novo_peso
    }])

    st.session_state.historico_peso = pd.concat(
        [st.session_state.historico_peso, novo_registro],
        ignore_index=True
    )

st.sidebar.markdown("---")

st.sidebar.metric("TMB", f"{TMB:.0f} kcal")
st.sidebar.metric("GET", f"{GET:.0f} kcal")
st.sidebar.metric("Meta Emagrecimento", f"{META_KCAL:.0f} kcal")
st.sidebar.metric("Meta Água", f"{META_AGUA:.0f} ml")

# =========================================================
# TABS
# =========================================================

tabs = st.tabs([
    "🍽️ Alimentação",
    "🏋️ Exercícios",
    "📈 Evolução",
    "📚 Banco",
    "📊 Relatórios"
])

# =========================================================
# ABA ALIMENTAÇÃO
# =========================================================

with tabs[0]:

    st.title("🍽️ Alimentação")

    alimentos_df = st.session_state.alimentos

    alimento_escolhido = st.selectbox(
        "Escolha o alimento",
        alimentos_df["Alimento"].tolist()
    )

    alimento_info = alimentos_df[
        alimentos_df["Alimento"] == alimento_escolhido
    ].iloc[0]

    tipo = alimento_info["Tipo"]

    if tipo == "g":
        quantidade = st.number_input(
            "Quantidade (g)",
            min_value=1.0,
            value=100.0
        )

        calorias = quantidade * alimento_info["Kcal_g"]

    else:
        quantidade = st.number_input(
            "Quantidade (un)",
            min_value=1.0,
            value=1.0
        )

        calorias = quantidade * alimento_info["Kcal_g"]

    st.metric("Calorias", f"{calorias:.0f} kcal")

    if st.button("➕ Adicionar ao prato"):
        st.session_state.carrinho.append({
            "Alimento": alimento_escolhido,
            "Quantidade": quantidade,
            "Calorias": calorias
        })

    st.markdown("## 🛒 Meu Prato")

    total_prato = 0

    if len(st.session_state.carrinho) > 0:

        for i, item in enumerate(st.session_state.carrinho):

            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

            col1.write(item["Alimento"])
            col2.write(f'{item["Quantidade"]}')
            col3.write(f'{item["Calorias"]:.0f} kcal')

            if col4.button("🗑️", key=f"del_cart_{i}"):
                st.session_state.carrinho.pop(i)
                st.rerun()

            total_prato += item["Calorias"]

        st.metric("Total do Prato", f"{total_prato:.0f} kcal")

        refeicao = st.selectbox(
            "Categoria da Refeição",
            ["Café da Manhã", "Almoço", "Lanche", "Janta", "Ceia"]
        )

        if st.button("✅ Registrar Refeição"):

            novos_itens = []

            for item in st.session_state.carrinho:
                novos_itens.append({
                    "Data": datetime.now(),
                    "Refeicao": refeicao,
                    "Alimento": item["Alimento"],
                    "Quantidade": item["Quantidade"],
                    "Calorias": item["Calorias"]
                })

            novo_df = pd.DataFrame(novos_itens)

            st.session_state.historico_refeicoes = pd.concat(
                [st.session_state.historico_refeicoes, novo_df],
                ignore_index=True
            )

            st.session_state.carrinho = []

            st.success("Refeição registrada!")
            st.rerun()

    st.markdown("---")
    st.markdown("## 📋 Histórico")

    historico = st.session_state.historico_refeicoes

    if not historico.empty:

        categorias = historico["Refeicao"].unique()

        for cat in categorias:

            with st.expander(cat, expanded=True):

                df_cat = historico[historico["Refeicao"] == cat]

                for idx, row in df_cat.iterrows():

                    c1, c2, c3, c4 = st.columns([3, 2, 2, 1])

                    c1.write(row["Alimento"])
                    c2.write(row["Quantidade"])
                    c3.write(f'{row["Calorias"]:.0f} kcal')

                    if c4.button("🗑️", key=f"hist_{idx}"):

                        st.session_state.historico_refeicoes = (
                            st.session_state.historico_refeicoes.drop(idx)
                        )

                        st.rerun()

# =========================================================
# ABA EXERCÍCIOS
# =========================================================

with tabs[1]:

    st.title("🏋️ Exercícios")

    METS = {
        "Musculação": 6,
        "Corrida": 9.8,
        "Caminhada": 3.8
    }

    atividade = st.selectbox(
        "Atividade",
        list(METS.keys()) + ["Gasto Manual"]
    )

    if atividade != "Gasto Manual":

        duracao = st.number_input(
            "Duração (min)",
            min_value=1,
            value=60
        )

        met = METS[atividade]

        calorias = (
            met * 3.5 * st.session_state.peso_atual / 200
        ) * duracao

        st.metric("Gasto Calórico", f"{calorias:.0f} kcal")

        if st.button("Registrar Exercício"):

            novo = pd.DataFrame([{
                "Data": datetime.now(),
                "Atividade": atividade,
                "Duracao": duracao,
                "Calorias": calorias
            }])

            st.session_state.historico_exercicios = pd.concat(
                [st.session_state.historico_exercicios, novo],
                ignore_index=True
            )

            st.success("Exercício registrado!")

    else:

        descricao = st.text_input("Descrição")

        kcal_manual = st.number_input(
            "Calorias Gastas",
            min_value=0.0,
            value=100.0
        )

        if st.button("Registrar Gasto Manual"):

            novo = pd.DataFrame([{
                "Data": datetime.now(),
                "Atividade": descricao,
                "Duracao": 0,
                "Calorias": kcal_manual
            }])

            st.session_state.historico_exercicios = pd.concat(
                [st.session_state.historico_exercicios, novo],
                ignore_index=True
            )

            st.success("Gasto registrado!")

    st.markdown("---")

    st.subheader("Histórico de Exercícios")

    if not st.session_state.historico_exercicios.empty:
        st.dataframe(
            st.session_state.historico_exercicios,
            use_container_width=True
        )

# =========================================================
# ABA EVOLUÇÃO
# =========================================================

with tabs[2]:

    st.title("📈 Evolução do Peso")

    hist_peso = st.session_state.historico_peso.copy()

    fig = px.line(
        hist_peso,
        x="Data",
        y="Peso",
        markers=True,
        title="Evolução do Peso"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(hist_peso, use_container_width=True)

# =========================================================
# ABA BANCO DE ALIMENTOS
# =========================================================

with tabs[3]:

    st.title("📚 Banco de Alimentos")

    with st.form("novo_alimento"):

        nome = st.text_input("Nome do alimento")

        tipo = st.selectbox(
            "Tipo",
            ["g", "un"]
        )

        kcal = st.number_input(
            "Calorias por 100g ou unidade",
            min_value=0.0
        )

        submit = st.form_submit_button("Salvar")

        if submit:

            if tipo == "g":
                kcal_g = kcal / 100
            else:
                kcal_g = kcal

            novo = pd.DataFrame([{
                "Alimento": nome,
                "Tipo": tipo,
                "Kcal_base": kcal,
                "Kcal_g": kcal_g
            }])

            st.session_state.alimentos = pd.concat(
                [st.session_state.alimentos, novo],
                ignore_index=True
            )

            st.success("Alimento cadastrado!")

    st.markdown("---")

    st.dataframe(
        st.session_state.alimentos,
        use_container_width=True
    )

# =========================================================
# ABA RELATÓRIOS
# =========================================================

with tabs[4]:

    st.title("📊 Relatórios")

    total_ingerido = (
        st.session_state.historico_refeicoes["Calorias"].sum()
        if not st.session_state.historico_refeicoes.empty
        else 0
    )

    total_exercicios = (
        st.session_state.historico_exercicios["Calorias"].sum()
        if not st.session_state.historico_exercicios.empty
        else 0
    )

    total_queimado = GET + total_exercicios

    col1, col2 = st.columns(2)

    col1.metric(
        "🔥 Total Queimado",
        f"{total_queimado:.0f} kcal"
    )

    col2.metric(
        "🍔 Total Ingerido",
        f"{total_ingerido:.0f} kcal"
    )

    saldo = total_ingerido - total_queimado

    st.metric(
        "⚖️ Saldo Calórico",
        f"{saldo:.0f} kcal"
    )

    grafico_df = pd.DataFrame({
        "Categoria": ["Ingerido", "Queimado"],
        "Calorias": [total_ingerido, total_queimado]
    })

    fig = px.bar(
        grafico_df,
        x="Categoria",
        y="Calorias",
        title="Comparativo Calórico"
    )

    st.plotly_chart(fig, use_container_width=True)

# =========================================================
# RODAPÉ
# =========================================================

st.markdown("---")
st.caption("Sistema de Gestão de Saúde e Emagrecimento")

# app.py
import streamlit as st
import pandas as pd
import datetime as dt

# ---------------------------------------------------------
# CONFIGURAÇÃO DO APP
# ---------------------------------------------------------
st.set_page_config(page_title="Gestão Saúde & Emagrecimento", layout="wide")

SEXO = "M"
IDADE = 30
ALTURA_CM = 186
PESO_INICIAL = 107.0

# ---------------------------------------------------------
# FUNÇÕES AUXILIARES
# ---------------------------------------------------------
def init_state():
    if "peso_atual" not in st.session_state:
        st.session_state.peso_atual = PESO_INICIAL

    if "historico_peso" not in st.session_state:
        st.session_state.historico_peso = pd.DataFrame(
            [{"data": dt.date.today(), "peso": PESO_INICIAL}]
        )

    if "banco_alimentos" not in st.session_state:
        st.session_state.banco_alimentos = pd.DataFrame(
            [
                {"nome": "Arroz cozido", "kcal_por_g": 1.3},
                {"nome": "Feijão cozido", "kcal_por_g": 1.0},
                {"nome": "Frango grelhado", "kcal_por_g": 1.65},
                {"nome": "Ovo cozido", "kcal_por_g": 1.55},
            ]
        )

    if "carrinho" not in st.session_state:
        st.session_state.carrinho = []

    if "historico_refeicoes" not in st.session_state:
        st.session_state.historico_refeicoes = pd.DataFrame(
            columns=["data", "hora", "categoria", "alimento", "qtd_g", "kcal"]
        )

    if "historico_exercicios" not in st.session_state:
        st.session_state.historico_exercicios = pd.DataFrame(
            columns=["data", "hora", "descricao", "kcal"]
        )


def calcular_tmb(peso, altura, idade, sexo="M"):
    if sexo == "M":
        return 10 * peso + 6.25 * altura - 5 * idade + 5
    return 10 * peso + 6.25 * altura - 5 * idade - 161


def calcular_get(tmb, fator):
    return tmb * fator


def metas(peso, tmb, get):
    return get - 500, peso * 35


def registrar_peso_diario(peso):
    hoje = dt.date.today()
    df = st.session_state.historico_peso

    if hoje not in df["data"].values:
        novo = pd.DataFrame([{"data": hoje, "peso": peso}])
        st.session_state.historico_peso = pd.concat([df, novo], ignore_index=True)


def registrar_peso_manual(peso):
    hoje = dt.date.today()
    df = st.session_state.historico_peso
    novo = pd.DataFrame([{"data": hoje, "peso": peso}])
    st.session_state.historico_peso = pd.concat([df, novo], ignore_index=True)
    st.session_state.peso_atual = peso


def registrar_refeicao(categoria):
    if not st.session_state.carrinho:
        return

    hoje = dt.date.today()
    hora = dt.datetime.now().strftime("%H:%M")

    novos = []
    for item in st.session_state.carrinho:
        novos.append(
            {
                "data": hoje,
                "hora": hora,
                "categoria": categoria,
                "alimento": item["alimento"],
                "qtd_g": item["qtd_g"],
                "kcal": item["kcal"],
            }
        )

    df = pd.DataFrame(novos)
    st.session_state.historico_refeicoes = pd.concat(
        [st.session_state.historico_refeicoes, df], ignore_index=True
    )
    st.session_state.carrinho = []


def registrar_exercicio(desc, kcal):
    hoje = dt.date.today()
    hora = dt.datetime.now().strftime("%H:%M")
    df = st.session_state.historico_exercicios
    novo = pd.DataFrame([{"data": hoje, "hora": hora, "descricao": desc, "kcal": kcal}])
    st.session_state.historico_exercicios = pd.concat([df, novo], ignore_index=True)


def adicionar_alimento(nome, kcal, base):
    if base == "100g":
        kcal_por_g = kcal / 100
    else:
        kcal_por_g = kcal

    df = st.session_state.banco_alimentos
    novo = pd.DataFrame([{"nome": nome, "kcal_por_g": kcal_por_g}])
    st.session_state.banco_alimentos = pd.concat([df, novo], ignore_index=True)


# ---------------------------------------------------------
# INICIALIZAÇÃO
# ---------------------------------------------------------
init_state()
registrar_peso_diario(st.session_state.peso_atual)

peso_atual = st.session_state.peso_atual

# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------
st.sidebar.title("Perfil & Metas")

novo_peso = st.sidebar.number_input(
    "Registrar peso de hoje (kg)", min_value=40.0, max_value=250.0, value=peso_atual
)

if st.sidebar.button("Salvar peso"):
    registrar_peso_manual(novo_peso)
    st.sidebar.success("Peso registrado!")

fator = st.sidebar.selectbox(
    "Nível de atividade",
    [
        ("Sedentário (1.2)", 1.2),
        ("Leve (1.375)", 1.375),
        ("Moderado (1.55)", 1.55),
        ("Ativo (1.725)", 1.725),
        ("Muito ativo (1.9)", 1.9),
    ],
    format_func=lambda x: x[0],
)[1]

tmb = calcular_tmb(peso_atual, ALTURA_CM, IDADE, SEXO)
get = calcular_get(tmb, fator)
meta_cal, meta_agua = metas(peso_atual, tmb, get)

st.sidebar.metric("TMB", f"{tmb:.0f} kcal")
st.sidebar.metric("GET", f"{get:.0f} kcal")
st.sidebar.metric("Meta Calorias", f"{meta_cal:.0f} kcal")
st.sidebar.metric("Meta Água", f"{meta_agua/1000:.2f} L")

# ---------------------------------------------------------
# TABS
# ---------------------------------------------------------
tab_evo, tab_alim, tab_ex, tab_hist, tab_banco, tab_rel = st.tabs(
    ["Evolução", "Alimentação", "Exercícios", "Histórico", "Banco", "Relatórios"]
)

# ---------------------------------------------------------
# EVOLUÇÃO
# ---------------------------------------------------------
with tab_evo:
    st.header("Evolução de Peso")
    df = st.session_state.historico_peso.sort_values("data")
    st.line_chart(df.set_index("data")["peso"])
    st.dataframe(df, use_container_width=True)

# ---------------------------------------------------------
# ALIMENTAÇÃO
# ---------------------------------------------------------
with tab_alim:
    st.header("Registrar Refeição")

    # 🔍 FILTRO DE BUSCA
    busca = st.text_input("Buscar alimento")
    df_banco = st.session_state.banco_alimentos

    if busca:
        df_banco = df_banco[df_banco["nome"].str.contains(busca, case=False)]

    alimento = st.selectbox("Alimento", df_banco["nome"].tolist())

    unidade = st.radio("Unidade", ["g", "unidade"], horizontal=True)
    qtd = st.number_input("Quantidade", min_value=1.0, value=100.0)

    kcal_g = float(df_banco[df_banco["nome"] == alimento]["kcal_por_g"].iloc[0])
    qtd_g = qtd if unidade == "g" else qtd
    kcal_total = qtd_g * kcal_g

    st.markdown(f"**Calorias:** {kcal_total:.0f} kcal")

    if st.button("Adicionar ao prato"):
        st.session_state.carrinho.append(
            {"alimento": alimento, "qtd_g": qtd_g, "kcal": kcal_total}
        )

    st.subheader("Carrinho")
    total = 0
    for i, item in enumerate(st.session_state.carrinho):
        cols = st.columns([4, 2, 2, 1])
        cols[0].write(item["alimento"])
        cols[1].write(f"{item['qtd_g']:.0f} g")
        cols[2].write(f"{item['kcal']:.0f} kcal")
        total += item["kcal"]
        if cols[3].button("🗑️", key=f"del_{i}"):
            st.session_state.carrinho.pop(i)
            st.experimental_rerun()

    st.write(f"**Total do prato:** {total:.0f} kcal")

    categoria = st.selectbox(
        "Categoria",
        ["Café da manhã", "Lanche manhã", "Almoço", "Lanche tarde", "Jantar", "Ceia"],
    )

    if st.button("Registrar refeição"):
        registrar_refeicao(categoria)
        st.success("Refeição registrada!")
        st.experimental_rerun()

# ---------------------------------------------------------
# EXERCÍCIOS
# ---------------------------------------------------------
with tab_ex:
    st.header("Exercícios")

    met_dict = {"Musculação": 6, "Corrida": 9.8, "Caminhada": 3.5}

    atividade = st.selectbox("Atividade", list(met_dict.keys()))
    dur = st.number_input("Duração (min)", min_value=5, value=30)

    kcal = met_dict[atividade] * 3.5 * peso_atual / 200 * dur
    st.write(f"**Gasto estimado:** {kcal:.0f} kcal")

    if st.button("Registrar exercício"):
        registrar_exercicio(atividade, kcal)
        st.success("Exercício registrado!")

    st.subheader("Gasto manual")
    desc = st.text_input("Descrição")
    kcal_m = st.number_input("Calorias", min_value=1.0, value=100.0)

    if st.button("Registrar gasto manual"):
        registrar_exercicio(desc, kcal_m)
        st.success("Gasto registrado!")

# ---------------------------------------------------------
# HISTÓRICO
# ---------------------------------------------------------
with tab_hist:
    st.header("Histórico Completo")

    df_ref = st.session_state.historico_refeicoes
    df_ex = st.session_state.historico_exercicios

    st.subheader("Refeições")
    st.dataframe(df_ref, use_container_width=True)

    st.subheader("Exercícios")
    st.dataframe(df_ex, use_container_width=True)

# ---------------------------------------------------------
# BANCO
# ---------------------------------------------------------
with tab_banco:
    st.header("Banco de Alimentos")

    nome = st.text_input("Nome")
    base = st.radio("Base", ["100g", "unidade"], horizontal=True)
    kcal = st.number_input("Calorias", min_value=1.0, value=100.0)

    if st.button("Adicionar alimento"):
        adicionar_alimento(nome, kcal, base)
        st.success("Adicionado!")

    st.dataframe(st.session_state.banco_alimentos.sort_values("nome"))

# ---------------------------------------------------------
# RELATÓRIOS
# ---------------------------------------------------------
with tab_rel:
    st.header("Relatórios")

    df_ref = st.session_state.historico_refeicoes
    df_ex = st.session_state.historico_exercicios

    dias = sorted(df_ref["data"].unique())

    dia_sel = st.selectbox("Selecionar dia", dias)

    df_dia_ref = df_ref[df_ref["data"] == dia_sel]
    df_dia_ex = df_ex[df_ex["data"] == dia_sel]

    ingerido = df_dia_ref["kcal"].sum()
    queimado = df_dia_ex["kcal"].sum()

    st.metric("Ingerido", f"{ingerido:.0f} kcal")
    st.metric("Queimado", f"{queimado:.0f} kcal")
    st.metric("Saldo", f"{ingerido - queimado:.0f} kcal")

    st.subheader("Comparativo")
    df_bar = pd.DataFrame(
        {"Tipo": ["Ingerido", "Queimado"], "kcal": [ingerido, queimado]}
    ).set_index("Tipo")

    st.bar_chart(df_bar)

    st.subheader("Resumo semanal")
    df_ref["semana"] = df_ref["data"].dt.isocalendar().week
    df_ex["semana"] = df_ex["data"].dt.isocalendar().week

    semana_sel = st.selectbox("Semana", sorted(df_ref["semana"].unique()))

    ing_sem = df_ref[df_ref["semana"] == semana_sel]["kcal"].sum()
    que_sem = df_ex[df_ex["semana"] == semana_sel]["kcal"].sum()

    st.write(f"**Ingerido na semana:** {ing_sem:.0f} kcal")
    st.write(f"**Queimado na semana:** {que_sem:.0f} kcal")

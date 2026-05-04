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
            [{"data": pd.to_datetime(dt.date.today()), "peso": PESO_INICIAL}]
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
    hoje = pd.to_datetime(dt.date.today())
    df = st.session_state.historico_peso
    df = df[df["data"] != hoje]
    novo = pd.DataFrame([{"data": hoje, "peso": peso}])
    st.session_state.historico_peso = pd.concat([df, novo], ignore_index=True)
    st.session_state.peso_atual = peso


def registrar_refeicao(categoria):
    if not st.session_state.carrinho:
        return
    hoje = pd.to_datetime(dt.date.today())
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
    hoje = pd.to_datetime(dt.date.today())
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
peso_atual = st.session_state.peso_atual


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------
st.sidebar.title("Metas do Dia")

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
tab_peso, tab_evo, tab_alim, tab_ex, tab_hist, tab_banco, tab_rel = st.tabs(
    ["Peso Diário", "Evolução", "Alimentação", "Exercícios", "Histórico", "Banco", "Relatórios"]
)


# ---------------------------------------------------------
# PESO DIÁRIO
# ---------------------------------------------------------
with tab_peso:
    st.header("Registro Diário de Peso")

    peso_hoje = st.number_input(
        "Seu peso de hoje (kg)",
        min_value=40.0,
        max_value=250.0,
        value=float(peso_atual),
        step=0.1,
        key="peso_do_dia",
    )

    if st.button("Registrar peso de hoje", key="btn_reg_peso"):
        registrar_peso_diario(peso_hoje)
        st.success("Peso registrado com sucesso!")

    st.subheader("Histórico de Peso")
    df_peso = st.session_state.historico_peso.sort_values("data")
    st.line_chart(df_peso.set_index("data")["peso"])
    st.dataframe(df_peso, use_container_width=True)


# ---------------------------------------------------------
# EVOLUÇÃO
# ---------------------------------------------------------
with tab_evo:
    st.header("Evolução de Peso")
    df_peso = st.session_state.historico_peso.sort_values("data")
    st.line_chart(df_peso.set_index("data")["peso"])
    st.dataframe(df_peso, use_container_width=True)


# ---------------------------------------------------------
# ALIMENTAÇÃO
# ---------------------------------------------------------
with tab_alim:
    st.header("Registrar Refeição")

    busca = st.text_input("Buscar alimento", key="busca_alimento")
    df_banco = st.session_state.banco_alimentos

    if busca:
        df_banco = df_banco[df_banco["nome"].str.contains(busca, case=False)]

    if df_banco.empty:
        st.warning("Nenhum alimento encontrado.")
    else:
        alimento = st.selectbox("Alimento", df_banco["nome"].tolist(), key="sel_alimento")

        unidade = st.radio("Unidade", ["g", "unidade"], horizontal=True, key="unidade_alimento")
        qtd = st.number_input(
            "Quantidade",
            min_value=1.0,
            value=100.0,
            step=1.0,
            key="qtd_alimento",
        )

        kcal_g = float(df_banco[df_banco["nome"] == alimento]["kcal_por_g"].iloc[0])
        qtd_g = qtd if unidade == "g" else qtd
        kcal_total = qtd_g * kcal_g

        st.markdown(f"**Calorias deste item:** {kcal_total:.0f} kcal")

        if st.button("Adicionar ao prato", key="btn_add_prato"):
            st.session_state.carrinho.append(
                {"alimento": alimento, "qtd_g": qtd_g, "kcal": kcal_total}
            )

    st.subheader("Carrinho")
    total = 0
    remove_index = None

    for i, item in enumerate(st.session_state.carrinho):
        cols = st.columns([4, 2, 2, 1])
        cols[0].write(item["alimento"])
        cols[1].write(f"{item['qtd_g']:.0f} g/un")
        cols[2].write(f"{item['kcal']:.0f} kcal")
        total += item["kcal"]
        if cols[3].button("🗑️", key=f"del_carrinho_{i}"):
            remove_index = i

    if remove_index is not None:
        st.session_state.carrinho.pop(remove_index)

    st.write(f"**Total do prato:** {total:.0f} kcal")

    categoria = st.selectbox(
        "Categoria da refeição",
        ["Café da manhã", "Lanche manhã", "Almoço", "Lanche tarde", "Jantar", "Ceia"],
        key="categoria_refeicao",
    )

    if st.button("Registrar refeição", key="btn_reg_refeicao"):
        if not st.session_state.carrinho:
            st.warning("Adicione itens ao prato antes de registrar.")
        else:
            registrar_refeicao(categoria)
            st.success("Refeição registrada!")


# ---------------------------------------------------------
# EXERCÍCIOS
# ---------------------------------------------------------
with tab_ex:
    st.header("Exercícios")

    met_dict = {"Musculação": 6, "Corrida": 9.8, "Caminhada": 3.5}

    atividade = st.selectbox("Atividade", list(met_dict.keys()), key="atividade_ex")
    dur = st.number_input(
        "Duração (min)",
        min_value=5,
        value=30,
        step=5,
        key="duracao_ex",
    )

    kcal_est = met_dict[atividade] * 3.5 * peso_atual / 200 * dur
    st.write(f"**Gasto estimado:** {kcal_est:.0f} kcal")

    if st.button("Registrar exercício", key="btn_reg_ex"):
        registrar_exercicio(atividade, kcal_est)
        st.success("Exercício registrado!")

    st.subheader("Gasto manual")
    desc = st.text_input("Descrição da atividade", key="desc_ex_manual")
    kcal_m = st.number_input(
        "Calorias gastas (kcal)",
        min_value=1.0,
        value=100.0,
        step=10.0,
        key="kcal_manual_exercicio",
    )

    if st.button("Registrar gasto manual", key="btn_reg_ex_manual"):
        if desc.strip() == "":
            st.warning("Informe uma descrição.")
        else:
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

    nome = st.text_input("Nome do alimento", key="nome_banco")
    base = st.radio("Base de cálculo", ["100g", "unidade"], horizontal=True, key="base_banco")
    kcal = st.number_input(
        "Calorias da base escolhida",
        min_value=1.0,
        value=100.0,
        step=10.0,
        key="kcal_banco_alimento",
    )

    if st.button("Adicionar alimento", key="btn_add_alimento"):
        if nome.strip() == "":
            st.warning("Informe o nome do alimento.")
        else:
            adicionar_alimento(nome, kcal, base)
            st.success("Alimento adicionado!")

    st.subheader("Alimentos cadastrados")
    st.dataframe(st.session_state.banco_alimentos.sort_values("nome"), use_container_width=True)


# ---------------------------------------------------------
# RELATÓRIOS
# ---------------------------------------------------------
with tab_rel:
    st.header("Relatórios")

    df_ref = st.session_state.historico_refeicoes.copy()
    df_ex = st.session_state.historico_exercicios.copy()

    if not df_ref.empty:
        df_ref["data"] = pd.to_datetime(df_ref["data"], errors="coerce")
    if not df_ex.empty:
        df_ex["data"] = pd.to_datetime(df_ex["data"], errors="coerce")

    dias = sorted(df_ref["data"].dropna().unique()) if not df_ref.empty else []

    if dias:
        dia_sel = st.selectbox("Selecionar dia", dias, key="dia_rel")
        df_dia_ref = df_ref[df_ref["data"] == dia_sel]
        df_dia_ex = df_ex[df_ex["data"] == dia_sel]

        ingerido = df_dia_ref["kcal"].sum()
        queimado = df_dia_ex["kcal"].sum()

        col1, col2, col3 = st.columns(3)
        col1.metric("Ingerido", f"{ingerido:.0f} kcal")
        col2.metric("Queimado", f"{queimado:.0f} kcal")
        col3.metric("Saldo", f"{ingerido - queimado:.0f} kcal")

        st.subheader("Comparativo Ingerido x Queimado")
        df_bar = pd.DataFrame(
            {"Tipo": ["Ingerido", "Queimado"], "kcal": [ingerido, queimado]}
        ).set_index("Tipo")
        st.bar_chart(df_bar)

    st.subheader("Resumo semanal")

    if not df_ref.empty:
        df_ref["data"] = pd.to_datetime(df_ref["data"], errors="coerce")
        df_ex["data"] = pd.to_datetime(df_ex["data"], errors="coerce")

        df_ref["semana"] = df_ref["data"].dt.isocalendar().week
        df_ex["semana"] = df_ex["data"].dt.isocalendar().week

        semanas = sorted(df_ref["semana"].dropna().unique())
        if len(semanas) > 0:
            semana_sel = st.selectbox("Semana", semanas, key="semana_rel")

            ing_sem = df_ref[df_ref["semana"] == semana_sel]["kcal"].sum()
            que_sem = df_ex[df_ex["semana"] == semana_sel]["kcal"].sum()

            st.write(f"**Ingerido na semana:** {ing_sem:.0f} kcal")
            st.write(f"**Queimado na semana:** {que_sem:.0f} kcal")

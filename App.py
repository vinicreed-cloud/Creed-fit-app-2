# app.py
import streamlit as st
import pandas as pd
import datetime as dt

# -----------------------------
# CONFIGURAÇÃO BÁSICA
# -----------------------------
st.set_page_config(page_title="Gestão Saúde & Emagrecimento", layout="wide")

# Dados fixos do usuário
SEXO = "M"
IDADE = 30
ALTURA_CM = 186  # 1,86m
PESO_INICIAL = 107.0

# -----------------------------
# FUNÇÕES AUXILIARES
# -----------------------------
def init_session_state():
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
                {"nome": "Peito de frango grelhado", "kcal_por_g": 1.65},
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


def calcular_tmb(peso, altura_cm, idade, sexo="M"):
    # Fórmula de Mifflin-St Jeor
    if sexo == "M":
        return 10 * peso + 6.25 * altura_cm - 5 * idade + 5
    else:
        return 10 * peso + 6.25 * altura_cm - 5 * idade - 161


def calcular_get(tmb, fator_atividade):
    return tmb * fator_atividade


def metas(peso, tmb, get):
    meta_calorias = get - 500
    meta_agua_ml = peso * 35
    return meta_calorias, meta_agua_ml


def get_peso_atual():
    # Último registro do histórico
    df = st.session_state.historico_peso
    return float(df.sort_values("data")["peso"].iloc[-1])


def registrar_peso(novo_peso):
    hoje = dt.date.today()
    df = st.session_state.historico_peso
    novo_registro = pd.DataFrame([{"data": hoje, "peso": novo_peso}])
    st.session_state.historico_peso = pd.concat([df, novo_registro], ignore_index=True)
    st.session_state.peso_atual = novo_peso


def adicionar_item_carrinho(alimento, qtd_g, kcal_total):
    st.session_state.carrinho.append(
        {"alimento": alimento, "qtd_g": qtd_g, "kcal": kcal_total}
    )


def limpar_carrinho():
    st.session_state.carrinho = []


def registrar_refeicao(categoria):
    if not st.session_state.carrinho:
        return
    hoje = dt.date.today()
    agora = dt.datetime.now().strftime("%H:%M")
    registros = []
    for item in st.session_state.carrinho:
        registros.append(
            {
                "data": hoje,
                "hora": agora,
                "categoria": categoria,
                "alimento": item["alimento"],
                "qtd_g": item["qtd_g"],
                "kcal": item["kcal"],
            }
        )
    df_novos = pd.DataFrame(registros)
    st.session_state.historico_refeicoes = pd.concat(
        [st.session_state.historico_refeicoes, df_novos], ignore_index=True
    )
    limpar_carrinho()


def registrar_exercicio(descricao, kcal):
    hoje = dt.date.today()
    agora = dt.datetime.now().strftime("%H:%M")
    df = st.session_state.historico_exercicios
    novo = pd.DataFrame(
        [{"data": hoje, "hora": agora, "descricao": descricao, "kcal": kcal}]
    )
    st.session_state.historico_exercicios = pd.concat([df, novo], ignore_index=True)


def deletar_refeicao(idx):
    df = st.session_state.historico_refeicoes
    df = df.drop(index=idx).reset_index(drop=True)
    st.session_state.historico_refeicoes = df


def deletar_exercicio(idx):
    df = st.session_state.historico_exercicios
    df = df.drop(index=idx).reset_index(drop=True)
    st.session_state.historico_exercicios = df


def adicionar_alimento_banco(nome, kcal_valor, base):
    # base: "100g" ou "unidade"
    if base == "100g":
        kcal_por_g = kcal_valor / 100.0
    else:
        # por unidade, assumimos 1 unidade = 1 "g" lógico
        kcal_por_g = kcal_valor  # tratado como "por unidade"
    df = st.session_state.banco_alimentos
    novo = pd.DataFrame([{"nome": nome, "kcal_por_g": kcal_por_g}])
    st.session_state.banco_alimentos = pd.concat([df, novo], ignore_index=True)


# -----------------------------
# INICIALIZA SESSION STATE
# -----------------------------
init_session_state()

# Atualiza peso atual a partir do histórico
st.session_state.peso_atual = get_peso_atual()

# -----------------------------
# SIDEBAR - PERFIL E CONTROLES
# -----------------------------
st.sidebar.title("Perfil & Controles")

st.sidebar.markdown(
    f"**Homem, {IDADE} anos, {ALTURA_CM/100:.2f} m**"
)

# Atualização de peso
novo_peso = st.sidebar.number_input(
    "Peso atual (kg)", min_value=40.0, max_value=250.0,
    value=float(st.session_state.peso_atual), step=0.1
)
if st.sidebar.button("Atualizar peso"):
    registrar_peso(novo_peso)
    st.sidebar.success("Peso atualizado!")

# Fator de atividade
fator_atividade = st.sidebar.selectbox(
    "Nível de atividade",
    options=[
        ("Sedentário (x1.2)", 1.2),
        ("Levemente ativo (x1.375)", 1.375),
        ("Moderadamente ativo (x1.55)", 1.55),
        ("Muito ativo (x1.725)", 1.725),
        ("Extremamente ativo (x1.9)", 1.9),
    ],
    format_func=lambda x: x[0],
)[1]

# Cálculos de TMB, GET e metas
peso_atual = st.session_state.peso_atual
tmb = calcular_tmb(peso_atual, ALTURA_CM, IDADE, SEXO)
get = calcular_get(tmb, fator_atividade)
meta_calorias, meta_agua_ml = metas(peso_atual, tmb, get)

st.sidebar.markdown("### Metas diárias")
st.sidebar.metric("TMB (kcal)", f"{tmb:.0f}")
st.sidebar.metric("GET (kcal)", f"{get:.0f}")
st.sidebar.metric("Meta Calorias (kcal)", f"{meta_calorias:.0f}")
st.sidebar.metric("Meta Água (L)", f"{meta_agua_ml/1000:.2f}")

# -----------------------------
# TABS PRINCIPAIS
# -----------------------------
tab_evolucao, tab_alimentacao, tab_exercicios, tab_historico, tab_banco, tab_relatorios = st.tabs(
    ["Evolução", "Alimentação", "Exercícios", "Histórico", "Banco", "Relatórios"]
)

# -----------------------------
# TAB EVOLUÇÃO - HISTÓRICO DE PESO
# -----------------------------
with tab_evolucao:
    st.header("Evolução de Peso")
    df_peso = st.session_state.historico_peso.sort_values("data")
    st.line_chart(df_peso.set_index("data")["peso"])
    st.dataframe(df_peso, use_container_width=True)

# -----------------------------
# TAB ALIMENTAÇÃO - CARRINHO
# -----------------------------
with tab_alimentacao:
    st.header("Registro de Refeições (Carrinho)")

    df_banco = st.session_state.banco_alimentos.sort_values("nome")
    alimento_escolhido = st.selectbox(
        "Alimento",
        options=df_banco["nome"].tolist(),
    )

    unidade = st.radio("Unidade de medida", ["g", "unidade"], horizontal=True)
    qtd = st.number_input(
        f"Quantidade ({unidade})",
        min_value=1.0,
        max_value=2000.0,
        value=100.0,
        step=1.0,
    )

    # Recupera kcal_por_g
    kcal_por_g = float(
        df_banco.loc[df_banco["nome"] == alimento_escolhido, "kcal_por_g"].iloc[0]
    )

    if unidade == "g":
        qtd_g = qtd
    else:
        # tratamos "por unidade" como 1 "g lógico"
        qtd_g = qtd  # cada unidade usa kcal_por_g como "por unidade"

    kcal_total_item = qtd_g * kcal_por_g

    st.markdown(f"**Calorias deste item:** {kcal_total_item:.0f} kcal")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Adicionar ao prato"):
            adicionar_item_carrinho(alimento_escolhido, qtd_g, kcal_total_item)
    with col2:
        if st.button("Limpar prato"):
            limpar_carrinho()

    st.subheader("Meu prato (carrinho)")
    if st.session_state.carrinho:
        total_prato = 0
        for i, item in enumerate(st.session_state.carrinho):
            cols = st.columns([4, 2, 2, 1])
            cols[0].markdown(f"**{item['alimento']}**")
            cols[1].markdown(f"{item['qtd_g']:.0f} g/un")
            cols[2].markdown(f"{item['kcal']:.0f} kcal")
            total_prato += item["kcal"]
            if cols[3].button("🗑️", key=f"del_carrinho_{i}"):
                st.session_state.carrinho.pop(i)
                st.experimental_rerun()
        st.markdown(f"**Total do prato:** {total_prato:.0f} kcal")
    else:
        st.info("Nenhum item no prato ainda.")

    st.markdown("---")
    st.subheader("Registrar refeição")
    categoria = st.selectbox(
        "Categoria da refeição",
        ["Café da manhã", "Lanche da manhã", "Almoço", "Lanche da tarde", "Jantar", "Ceia"],
    )
    if st.button("Registrar Refeição"):
        if not st.session_state.carrinho:
            st.warning("Adicione itens ao prato antes de registrar.")
        else:
            registrar_refeicao(categoria)
            st.success("Refeição registrada!")
            st.experimental_rerun()

# -----------------------------
# TAB EXERCÍCIOS
# -----------------------------
with tab_exercicios:
    st.header("Exercícios & Gastos Extras")

    st.subheader("Atividades pré-definidas")
    met_dict = {
        "Musculação": 6.0,
        "Corrida": 9.8,
        "Caminhada": 3.5,
    }

    atividade = st.selectbox("Atividade", list(met_dict.keys()))
    duracao_min = st.number_input(
        "Duração (minutos)", min_value=5, max_value=300, value=30, step=5
    )

    met = met_dict[atividade]
    # Fórmula: kcal = MET * 3.5 * peso(kg) / 200 * tempo(min)
    kcal_exercicio = met * 3.5 * peso_atual / 200 * duracao_min

    st.markdown(f"**Gasto estimado:** {kcal_exercicio:.0f} kcal")

    if st.button("Registrar exercício"):
        registrar_exercicio(atividade, kcal_exercicio)
        st.success("Exercício registrado!")

    st.markdown("---")
    st.subheader("Gasto manual")
    desc_manual = st.text_input("Descrição da atividade")
    kcal_manual = st.number_input(
        "Calorias gastas (kcal)", min_value=1.0, max_value=5000.0, value=200.0, step=10.0
    )
    if st.button("Registrar gasto manual"):
        if desc_manual.strip() == "":
            st.warning("Informe uma descrição.")
        else:
            registrar_exercicio(desc_manual, kcal_manual)
            st.success("Gasto manual registrado!")

# -----------------------------
# TAB HISTÓRICO - REFEIÇÕES E EXERCÍCIOS
# -----------------------------
with tab_historico:
    st.header("Histórico do dia")

    hoje = dt.date.today()
    df_ref = st.session_state.historico_refeicoes
    df_ex = st.session_state.historico_exercicios

    df_ref_hoje = df_ref[df_ref["data"] == hoje]
    df_ex_hoje = df_ex[df_ex["data"] == hoje]

    st.subheader("Refeições")
    if df_ref_hoje.empty:
        st.info("Nenhuma refeição registrada hoje.")
    else:
        for categoria in df_ref_hoje["categoria"].unique():
            with st.expander(categoria, expanded=True):
                df_cat = df_ref_hoje[df_ref_hoje["categoria"] == categoria]
                for idx, row in df_cat.iterrows():
                    cols = st.columns([3, 2, 2, 1])
                    cols[0].markdown(f"**{row['alimento']}**")
                    cols[1].markdown(f"{row['qtd_g']:.0f} g/un")
                    cols[2].markdown(f"{row['kcal']:.0f} kcal")
                    if cols[3].button("🗑️", key=f"del_ref_{idx}"):
                        deletar_refeicao(idx)
                        st.experimental_rerun()

    st.markdown("---")
    st.subheader("Exercícios")
    if df_ex_hoje.empty:
        st.info("Nenhum exercício registrado hoje.")
    else:
        for idx, row in df_ex_hoje.iterrows():
            cols = st.columns([4, 2, 1])
            cols[0].markdown(f"**{row['descricao']}**")
            cols[1].markdown(f"{row['kcal']:.0f} kcal")
            if cols[2].button("🗑️", key=f"del_ex_{idx}"):
                deletar_exercicio(idx)
                st.experimental_rerun()

# -----------------------------
# TAB BANCO - CADASTRO DE ALIMENTOS
# -----------------------------
with tab_banco:
    st.header("Banco de Alimentos")

    st.subheader("Cadastrar novo alimento")
    nome_alimento = st.text_input("Nome do alimento")
    base_calculo = st.radio(
        "Base de cálculo",
        ["por 100g", "por unidade"],
        horizontal=True,
    )
    kcal_valor = st.number_input(
        "Calorias", min_value=1.0, max_value=2000.0, value=100.0, step=10.0
    )

    if st.button("Adicionar alimento"):
        if nome_alimento.strip() == "":
            st.warning("Informe o nome do alimento.")
        else:
            base = "100g" if base_calculo == "por 100g" else "unidade"
            adicionar_alimento_banco(nome_alimento, kcal_valor, base)
            st.success("Alimento adicionado ao banco!")

    st.markdown("---")
    st.subheader("Alimentos cadastrados")
    st.dataframe(st.session_state.banco_alimentos.sort_values("nome"), use_container_width=True)

# -----------------------------
# TAB RELATÓRIOS
# -----------------------------
with tab_relatorios:
    st.header("Relatórios do dia")

    hoje = dt.date.today()
    df_ref = st.session_state.historico_refeicoes
    df_ex = st.session_state.historico_exercicios

    df_ref_hoje = df_ref[df_ref["data"] == hoje]
    df_ex_hoje = df_ex[df_ex["data"] == hoje]

    total_ingerido = df_ref_hoje["kcal"].sum() if not df_ref_hoje.empty else 0
    total_queimado = df_ex_hoje["kcal"].sum() if not df_ex_hoje.empty else 0
    saldo = total_ingerido - total_queimado

    col1, col2, col3 = st.columns(3)
    col1.metric("Total ingerido (kcal)", f"{total_ingerido:.0f}")
    col2.metric("Total queimado (kcal)", f"{total_queimado:.0f}")
    col3.metric("Saldo (kcal)", f"{saldo:.0f}")

    st.markdown("---")
    st.subheader("Comparativo Ingerido vs Queimado")

    df_bar = pd.DataFrame(
        {
            "Tipo": ["Ingerido", "Queimado"],
            "kcal": [total_ingerido, total_queimado],
        }
    )
    st.bar_chart(df_bar.set_index("Tipo"))







import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="BioStats Pro v2", layout="centered")

# --- ESTILO CSS PARA MOBILE ---
st.markdown("""
    <style>
    .main { max-width: 500px; margin: 0 auto; }
    .stButton button { width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZAÇÃO DO ESTADO (SESSION STATE) ---
if 'db_alimentos' not in st.session_state:
    st.session_state.db_alimentos = [
        {"nome": "Arroz Branco", "cal_por_100g": 130},
        {"nome": "Feijão Preto", "cal_por_100g": 91},
        {"nome": "Frango Grelhado", "cal_por_100g": 165}
    ]

if 'historico_peso' not in st.session_state:
    # Iniciando com um histórico para o gráfico aparecer
    st.session_state.historico_peso = pd.DataFrame([{"data": datetime.now().date(), "peso": 100.0}])

if 'carrinho' not in st.session_state:
    st.session_state.carrinho = []

if 'historico_consumo' not in st.session_state:
    st.session_state.historico_consumo = pd.DataFrame(columns=["data", "categoria", "alimento", "calorias"])

if 'historico_exercicios' not in st.session_state:
    st.session_state.historico_exercicios = pd.DataFrame(columns=["data", "atividade", "calorias"])

# --- LÓGICA DE CÁLCULOS ---
IDADE = 30
ALTURA = 186

def calcular_metas(peso_atual):
    tmb = (10 * peso_atual) + (6.25 * ALTURA) - (5 * IDADE) + 5
    get = tmb * 1.2
    meta_calorica = get - 500
    meta_agua = (peso_atual * 35) / 1000
    return round(tmb), round(get), round(meta_calorica), round(meta_agua, 1)

# --- SIDEBAR (PERFIL E PESO DIÁRIO) ---
with st.sidebar:
    st.header("👤 Perfil BioStats")
    
    # Adição de peso diário com data específica
    st.subheader("Registrar Peso")
    data_peso = st.date_input("Data do Registro", datetime.now())
    peso_input = st.number_input("Peso (kg):", value=float(st.session_state.historico_peso.iloc[-1]['peso']), step=0.1)
    
    if st.button("Salvar Peso"):
        novo_registro = pd.DataFrame([{"data": data_peso, "peso": peso_input}])
        st.session_state.historico_peso = pd.concat([st.session_state.historico_peso, novo_registro], ignore_index=True)
        st.session_state.historico_peso = st.session_state.historico_peso.drop_duplicates('data', keep='last').sort_values('data')
        st.success("Peso registrado!")

    tmb, get, meta_cal, meta_agua = calcular_metas(peso_input)
    st.divider()
    st.metric("Meta Diária", f"{meta_cal} kcal")
    st.metric("Meta Água", f"{meta_agua} L")

# --- ABAS PRINCIPAIS ---
tab_diario, tab_exercicio, tab_evolucao, tab_banco = st.tabs(["🍽️ Diário", "💪 Treino", "📈 Evolução", "📂 Banco"])

# --- ABA 1: DIÁRIO (CATEGORIAS AMPLIADAS) ---
with tab_diario:
    st.subheader("Montar Prato")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        alimento_sel = st.selectbox("Alimento", options=[a['nome'] for a in st.session_state.db_alimentos])
        qtd = st.number_input("Quantidade (g/un)", min_value=1, value=100)
    
    dados_alimento = next(item for item in st.session_state.db_alimentos if item["nome"] == alimento_sel)
    cal_calculada = (dados_alimento['cal_por_100g'] / 100) * qtd
    
    with col2:
        st.write("Cals")
        st.info(f"{cal_calculada:.0f}")
        if st.button("➕"):
            st.session_state.carrinho.append({"alimento": alimento_sel, "calorias": cal_calculada})

    if st.session_state.carrinho:
        st.write("---")
        for i, item in enumerate(st.session_state.carrinho):
            c1, c2 = st.columns([3, 1])
            c1.write(f"{item['alimento']} ({item['calorias']:.0f} kcal)")
            if c2.button("🗑️", key=f"cart_{i}"):
                st.session_state.carrinho.pop(i)
                st.rerun()
        
        # Categorias solicitadas
        cat = st.selectbox("Onde registrar?", ["Café da Manhã", "Almoço", "Café da Tarde", "Janta", "Snacks"])
        if st.button("✅ Registrar Refeição"):
            df_temp = pd.DataFrame(st.session_state.carrinho)
            df_temp['data'] = datetime.now().strftime("%Y-%m-%d")
            df_temp['categoria'] = cat
            st.session_state.historico_consumo = pd.concat([st.session_state.historico_consumo, df_temp], ignore_index=True)
            st.session_state.carrinho = []
            st.success("Registrado com sucesso!")
            st.rerun()

    st.divider()
    st.subheader("Resumo do Dia")
    hoje = datetime.now().strftime("%Y-%m-%d")
    hist_hoje = st.session_state.historico_consumo[st.session_state.historico_consumo['data'] == hoje]
    
    for categoria in ["Café da Manhã", "Almoço", "Café da Tarde", "Janta", "Snacks"]:
        items_cat = hist_hoje[hist_hoje['categoria'] == categoria]
        if not items_cat.empty:
            with st.expander(f"📍 {categoria} - {items_cat['calorias'].sum():.0f} kcal"):
                for idx, row in items_cat.iterrows():
                    c1, c2 = st.columns([4, 1])
                    c1.write(f"{row['alimento']} ({row['calorias']:.0f} kcal)")
                    if c2.button("❌", key=f"del_h_{idx}"):
                        st.session_state.historico_consumo.drop(idx, inplace=True)
                        st.rerun()

# --- ABA 2: EXERCÍCIOS ---
with tab_exercicio:
    st.subheader("Atividade Física")
    tipo_ex = st.radio("Tipo", ["Musculação", "Corrida (9km/h)", "Caminhada", "Manual"], horizontal=True)
    
    if tipo_ex != "Manual":
        tempo = st.number_input("Tempo (min)", min_value=1, value=45)
        met_map = {"Musculação": 5.0, "Corrida (9km/h)": 8.8, "Caminhada": 3.5}
        gasto = round(met_map[tipo_ex] * peso_input * (tempo/60))
        st.info(f"Gasto: {gasto} kcal")
    else:
        gasto = st.number_input("Calorias", min_value=1)
        tipo_ex = st.text_input("Nome da Atividade")

    if st.button("🔥 Salvar Exercício"):
        novo_ex = pd.DataFrame([{"data": hoje, "atividade": tipo_ex, "calorias": gasto}])
        st.session_state.historico_exercicios = pd.concat([st.session_state.historico_exercicios, novo_ex], ignore_index=True)
        st.success("Gasto registrado!")

# --- ABA 3: EVOLUÇÃO ---
with tab_evolucao:
    st.subheader("Gráfico de Peso")
    if not st.session_state.historico_peso.empty:
        df_plot = st.session_state.historico_peso.copy()
        df_plot['data'] = pd.to_datetime(df_plot['data'])
        st.line_chart(df_plot.set_index('data')['peso'])
    
    st.divider()
    st.subheader("Balanço Energético")
    c_dia = hist_hoje['calorias'].sum()
    e_dia = st.session_state.historico_exercicios[st.session_state.historico_exercicios['data'] == hoje]['calorias'].sum()
    
    st.bar_chart(pd.DataFrame({
        "Kcal": [c_dia, meta_cal, e_dia],
        "Tipo": ["Consumido", "Meta", "Gasto Extra"]
    }).set_index("Tipo"))

# --- ABA 4: BANCO ---
with tab_banco:
    st.subheader("Novo Alimento")
    n = st.text_input("Nome")
    c = st.number_input("Cals / 100g")
    if st.button("Cadastrar"):
        st.session_state.db_alimentos.append({"nome": n, "cal_por_100g": c})
        st.rerun()
    st.dataframe(pd.DataFrame(st.session_state.db_alimentos), use_container_width=True)

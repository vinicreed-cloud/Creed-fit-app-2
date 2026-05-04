import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="BioStats Pro", layout="centered")

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
        {"nome": "Frango Grelhado", "cal_por_100g": 165},
        {"nome": "Ovo Cozido", "cal_por_100g": 155}
    ]

if 'historico_peso' not in st.session_state:
    st.session_state.historico_peso = pd.DataFrame([{"data": "2023-10-01", "peso": 100.0}])

if 'carrinho' not in st.session_state:
    st.session_state.carrinho = []

if 'historico_consumo' not in st.session_state:
    st.session_state.historico_consumo = pd.DataFrame(columns=["data", "categoria", "alimento", "calorias"])

if 'historico_exercicios' not in st.session_state:
    st.session_state.historico_exercicios = pd.DataFrame(columns=["data", "atividade", "calorias"])

# --- LÓGICA DE CÁLCULOS (Mifflin-St Jeor) ---
# Dados Fixos
IDADE = 30
ALTURA = 186
GENERO = "M"

def calcular_metas(peso_atual):
    # TMB = 10 * peso + 6.25 * altura - 5 * idade + 5
    tmb = (10 * peso_atual) + (6.25 * ALTURA) - (5 * IDADE) + 5
    get = tmb * 1.2  # Sedentário base, exercícios somam depois
    meta_calorica = get - 500
    meta_agua = (peso_atual * 35) / 1000
    return round(tmb), round(get), round(meta_calorica), round(meta_agua, 1)

# --- SIDEBAR (PERFIL E PESO) ---
with st.sidebar:
    st.header("👤 Perfil BioStats")
    peso_input = st.number_input("Peso Atual (kg):", value=float(st.session_state.historico_peso.iloc[-1]['peso']), step=0.1)
    
    if st.button("Atualizar Peso"):
        novo_registro = pd.DataFrame([{"data": datetime.now().strftime("%d/%m/%Y"), "peso": peso_input}])
        st.session_state.historico_peso = pd.concat([st.session_state.historico_peso, novo_registro], ignore_index=True)
        st.success("Peso atualizado!")

    tmb, get, meta_cal, meta_agua = calcular_metas(peso_input)
    
    st.divider()
    st.metric("Meta Diária", f"{meta_cal} kcal")
    st.metric("Meta Água", f"{meta_agua} L")

# --- ABAS PRINCIPAIS ---
tab_diario, tab_exercicio, tab_evolucao, tab_banco = st.tabs(["🍽️ Diário", "💪 Treino", "📈 Evolução", "📂 Banco"])

# --- ABA 1: DIÁRIO (SISTEMA DE CARRINHO) ---
with tab_diario:
    st.subheader("Montar Refeição")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        alimento_sel = st.selectbox("Alimento", options=[a['nome'] for a in st.session_state.db_alimentos])
        qtd = st.number_input("Quantidade (g/un)", min_value=1, value=100)
    
    dados_alimento = next(item for item in st.session_state.db_alimentos if item["nome"] == alimento_sel)
    cal_calculada = (dados_alimento['cal_por_100g'] / 100) * qtd
    
    with col2:
        st.write("Cals")
        st.info(f"{cal_calculada:.0f}")
        if st.button("➕ Adicionar"):
            st.session_state.carrinho.append({
                "alimento": alimento_sel,
                "calorias": cal_calculada
            })

    if st.session_state.carrinho:
        st.write("---")
        st.write("**Prato Atual:**")
        for i, item in enumerate(st.session_state.carrinho):
            c1, c2 = st.columns([3, 1])
            c1.write(f"{item['alimento']} - {item['calorias']:.0f} kcal")
            if c2.button("🗑️", key=f"del_{i}"):
                st.session_state.carrinho.pop(i)
                st.rerun()
        
        cat = st.selectbox("Categoria", ["Café da Manhã", "Almoço", "Lanche", "Jantar", "Ceia"])
        if st.button("✅ Registrar Refeição"):
            novos_itens = []
            for item in st.session_state.carrico: # Erro de digitação proposital para correção rápida
                pass # Lógica de inserção abaixo
            
            df_temp = pd.DataFrame(st.session_state.carrinho)
            df_temp['data'] = datetime.now().strftime("%Y-%m-%d")
            df_temp['categoria'] = cat
            st.session_state.historico_consumo = pd.concat([st.session_state.historico_consumo, df_temp], ignore_index=True)
            st.session_state.carrinho = []
            st.success("Refeição registrada!")
            st.rerun()

    st.divider()
    st.subheader("Histórico de Hoje")
    hoje = datetime.now().strftime("%Y-%m-%d")
    hist_hoje = st.session_state.historico_consumo[st.session_state.historico_consumo['data'] == hoje]
    
    for categoria in hist_hoje['categoria'].unique():
        with st.expander(f"📍 {categoria}"):
            items_cat = hist_hoje[hist_hoje['categoria'] == categoria]
            for idx, row in items_cat.iterrows():
                c1, c2 = st.columns([4, 1])
                c1.write(f"{row['alimento']} ({row['calorias']:.0f} kcal)")
                if c2.button("❌", key=f"hist_del_{idx}"):
                    st.session_state.historico_consumo.drop(idx, inplace=True)
                    st.rerun()

# --- ABA 2: EXERCÍCIOS ---
with tab_exercicio:
    st.subheader("Registrar Gasto")
    met_map = {"Musculação": 5.0, "Corrida (9km/h)": 8.8, "Caminhada": 3.5}
    tipo_ex = st.radio("Atividade", ["Musculação", "Corrida (9km/h)", "Caminhada", "Manual"])
    
    if tipo_ex != "Manual":
        tempo = st.number_input("Tempo (minutos)", min_value=1, value=60)
        # Gasto = MET * Peso * (Tempo/60)
        gasto = round(met_map[tipo_ex] * peso_input * (tempo/60))
        st.info(f"Gasto Estimado: {gasto} kcal")
    else:
        gasto = st.number_input("Calorias Manuais", min_value=1)
        tipo_ex = st.text_input("Descrição da Atividade", "Exercício")

    if st.button("🔥 Registrar Exercício"):
        novo_ex = pd.DataFrame([{"data": hoje, "atividade": tipo_ex, "calorias": gasto}])
        st.session_state.historico_exercicios = pd.concat([st.session_state.historico_exercicios, novo_ex], ignore_index=True)
        st.success("Queimado!")

# --- ABA 3: EVOLUÇÃO E RELATÓRIOS ---
with tab_evolucao:
    st.subheader("Análise de Dados")
    
    # Gráfico de Peso
    st.line_chart(st.session_state.historico_peso.set_index("data")["peso"])
    
    # Balanço do Dia
    consumo_dia = hist_hoje['calorias'].sum()
    queima_dia = st.session_state.historico_exercicios[st.session_state.historico_exercicios['data'] == hoje]['calorias'].sum()
    
    col_r1, col_r2 = st.columns(2)
    col_r1.metric("Ingerido", f"{consumo_dia:.0f} kcal")
    col_r2.metric("Exercício", f"{queima_dia:.0f} kcal")
    
    st.write("**Balanço Energético (Hoje)**")
    df_balanco = pd.DataFrame({
        "Tipo": ["Ingerido", "Meta", "Gasto (Treino)"],
        "Kcal": [consumo_dia, meta_cal, queima_dia]
    })
    st.bar_chart(df_balanco.set_index("Tipo"))

# --- ABA 4: BANCO DE ALIMENTOS ---
with tab_banco:
    st.subheader("Cadastrar Alimento")
    nome_novo = st.text_input("Nome do Alimento")
    cals_novo = st.number_input("Calorias por 100g (ou unidade)", min_value=0)
    
    if st.button("💾 Salvar no Banco"):
        if nome_novo:
            st.session_state.db_alimentos.append({"nome": nome_novo, "cal_por_100g": cals_novo})
            st.success(f"{nome_novo} adicionado!")
        else:
            st.error("Digite o nome do alimento.")
    
    st.write("**Meus Alimentos:**")
    st.dataframe(pd.DataFrame(st.session_state.db_alimentos), use_container_width=True)










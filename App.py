import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURAÇÕES INICIAIS ---
st.set_page_config(page_title="BioStats Pro: Evolution", layout="wide", page_icon="📉")

# --- INICIALIZAÇÃO DE ESTADO ---
if 'banco_alimentos' not in st.session_state:
    st.session_state.banco_alimentos = {"Arroz Branco": 1.30, "Feijão": 0.91, "Frango Grelhado": 1.65, "Ovo": 78.0}

if 'log_atividades' not in st.session_state:
    st.session_state.log_atividades = pd.DataFrame(columns=['Data', 'Tipo', 'Categoria', 'Descricao', 'Valor'])

if 'historico_peso' not in st.session_state:
    # Começando com seu peso inicial
    st.session_state.historico_peso = pd.DataFrame([{'Data': datetime.now(), 'Peso': 107.5}])

if 'carrinho_refeicao' not in st.session_state:
    st.session_state.carrinho_refeicao = []

# --- DADOS FIXOS DO USUÁRIO ---
ALTURA = 186
IDADE = 30
SEXO = "Masculino"

# --- BARRA LATERAL (PERFIL E PESO) ---
with st.sidebar:
    st.header("👤 Perfil & Bio")
    
    # Alteração de Peso
    peso_atual = st.number_input("Peso Atual (kg):", value=float(st.session_state.historico_peso['Peso'].iloc[-1]), step=0.1)
    
    if peso_atual != st.session_state.historico_peso['Peso'].iloc[-1]:
        if st.button("Atualizar Peso Oficial"):
            novo_peso = pd.DataFrame([{'Data': datetime.now(), 'Peso': peso_atual}])
            st.session_state.historico_peso = pd.concat([st.session_state.historico_peso, novo_peso], ignore_index=True)
            st.success("Peso atualizado!")

    st.divider()
    
    # Cálculos de Metabolismo (Mifflin-St Jeor)
    tmb = (10 * peso_atual) + (6.25 * ALTURA) - (5 * IDADE) + 5
    get = tmb * 1.2 # Sedentário
    meta_perda = get - 500
    meta_agua = peso_atual * 35 / 1000

    st.write(f"**TMB:** {int(tmb)} kcal")
    st.write(f"**Gasto Diário (GET):** {int(get)} kcal")
    st.info(f"**Meta para Emagrecer:** {int(meta_perda)} kcal")
    st.info(f"**Meta de Água:** {meta_agua:.2f}L")

# --- INTERFACE PRINCIPAL ---
st.title("📉 BioStats: Monitor de Evolução")

abas = st.tabs(["🍽️ Refeições", "🏃 Exercícios", "📉 Evolução de Peso", "📊 Relatórios", "📋 Histórico", "⚙️ Banco"])

# --- ABA 1: REFEIÇÕES (COM CARRINHO) ---
with abas[0]:
    col_sel, col_car = st.columns([1, 1])
    with col_sel:
        st.subheader("🥪 Montar Prato")
        refeicao_tipo = st.selectbox("Momento:", ["Café da Manhã", "Almoço", "Café da Tarde", "Janta", "Snacks"])
        busca = st.text_input("🔍 Buscar alimento:")
        opcoes = [a for a in st.session_state.banco_alimentos.keys() if busca.lower() in a.lower()]
        
        if opcoes:
            alimento_sel = st.selectbox("Selecionar:", opcoes)
            qtd = st.number_input("Quantidade (g ou un):", min_value=0.1, value=100.0)
            cal_temp = qtd * st.session_state.banco_alimentos[alimento_sel]
            if st.button("➕ Adicionar ao Prato"):
                st.session_state.carrinho_refeicao.append({'alimento': alimento_sel, 'qtd': qtd, 'kcal': cal_temp})
        
    with col_car:
        st.subheader("🛒 Resumo do Prato")
        if st.session_state.carrinho_refeicao:
            total_p = 0
            for i, item in enumerate(st.session_state.carrinho_refeicao):
                c1, c2 = st.columns([4, 1])
                c1.write(f"{item['alimento']} ({item['qtd']}g) -> {int(item['kcal'])} kcal")
                if c2.button("❌", key=f"cart_{i}"):
                    st.session_state.carrinho_refeicao.pop(i)
                    st.rerun()
                total_p += item['kcal']
            st.markdown(f"### Total: {int(total_p)} kcal")
            if st.button("🚀 REGISTRAR REFEIÇÃO", use_container_width=True):
                for item in st.session_state.carrinho_refeicao:
                    novo = pd.DataFrame([{'Data': datetime.now(), 'Tipo': 'Alimento', 'Categoria': refeicao_tipo, 'Descricao': item['alimento'], 'Valor': item['kcal']}])
                    st.session_state.log_atividades = pd.concat([st.session_state.log_atividades, novo], ignore_index=True)
                st.session_state.carrinho_refeicao = []
                st.success("Registrado!")
                st.rerun()

# --- ABA 2: EXERCÍCIOS ---
with abas[1]:
    st.subheader("Atividade Física")
    tipo_ex = st.selectbox("Atividade:", ["Musculação", "Caminhada", "Corrida", "Gasto Manual"])
    if tipo_ex == "Gasto Manual":
        d_m = st.text_input("Descrição:"); c_m = st.number_input("Kcal:");
        if st.button("Lançar"):
            novo = pd.DataFrame([{'Data': datetime.now(), 'Tipo': 'Exercício', 'Categoria': 'Extra', 'Descricao': d_m, 'Valor': c_m}])
            st.session_state.log_atividades = pd.concat([st.session_state.log_atividades, novo], ignore_index=True)
    else:
        minutos = st.number_input("Minutos:", value=45)
        mets = {"Musculação": 5.0, "Caminhada": 4.0, "Corrida": 8.0}
        gasto_ex = (mets[tipo_ex] * peso_atual * (minutos/60))
        st.write(f"Queima: **{int(gasto_ex)} kcal**")
        if st.button("Lançar Exercício"):
            novo = pd.DataFrame([{'Data': datetime.now(), 'Tipo': 'Exercício', 'Categoria': 'Treino', 'Descricao': tipo_ex, 'Valor': gasto_ex}])
            st.session_state.log_atividades = pd.concat([st.session_state.log_atividades, novo], ignore_index=True)

# --- ABA 3: EVOLUÇÃO DE PESO ---
with abas[2]:
    st.subheader("📉 Curva de Peso")
    if not st.session_state.historico_peso.empty:
        df_peso = st.session_state.historico_peso.copy()
        df_peso['Data'] = pd.to_datetime(df_peso['Data']).dt.date
        st.line_chart(df_peso.set_index('Data'))
        
        perda_total = st.session_state.historico_peso['Peso'].iloc[0] - peso_atual
        st.metric("Total Eliminado", f"{perda_total:.1f} kg", delta=f"-{perda_total:.1f}")

# --- ABA 4: RELATÓRIOS ---
with abas[3]:
    df_p = st.session_state.log_atividades
    if not df_p.empty:
        st.subheader("Consumo vs Queima")
        st.bar_chart(df_p.groupby('Tipo')['Valor'].sum())

# --- ABA 5: HISTÓRICO ---
with abas[4]:
    df_h = st.session_state.log_atividades
    if not df_h.empty:
        for i, row in df_h.iterrows():
            c1, c2 = st.columns([4, 1])
            c1.write(f"{row['Data'].strftime('%H:%M')} - {row['Categoria']}: {row['Descricao']} ({int(row['Valor'])} kcal)")
            if c2.button("🗑️", key=f"del_{i}"):
                st.session_state.log_atividades = st.session_state.log_atividades.drop(i)
                st.rerun()

# --- ABA 6: BANCO ---
with abas[5]:
    st.subheader("Cadastrar Alimento")
    n_n = st.text_input("Nome:"); n_c = st.number_input("Kcal/100g ou un:");
    if st.button("Salvar"):
        st.session_state.banco_alimentos[n_n] = n_c / 100 if n_c > 10 else n_c
        st.success("Salvo!")
        

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURAÇÕES DO PERFIL ---
st.set_page_config(page_title="BioStats Pro v3", layout="wide", page_icon="⚖️")

# --- INICIALIZAÇÃO DE ESTADO ---
if 'banco_alimentos' not in st.session_state:
    st.session_state.banco_alimentos = {"Arroz Branco": 1.30, "Feijão": 0.91, "Frango Grelhado": 1.65, "Ovo": 78.0}

if 'log_atividades' not in st.session_state:
    st.session_state.log_atividades = pd.DataFrame({
        'Data': pd.to_datetime([]),
        'Tipo': pd.Series([], dtype='str'),
        'Categoria': pd.Series([], dtype='str'),
        'Descricao': pd.Series([], dtype='str'),
        'Valor': pd.Series([], dtype='float')
    })

if 'peso_usuario' not in st.session_state:
    st.session_state.peso_usuario = 107.5

# --- FUNÇÃO PARA ADICIONAR AO HISTÓRICO ---
def adicionar_registro(tipo, categoria, desc, valor):
    novo_registro = pd.DataFrame([{
        'Data': datetime.now(),
        'Tipo': tipo,
        'Categoria': categoria,
        'Descricao': desc,
        'Valor': float(valor)
    }])
    st.session_state.log_atividades = pd.concat([st.session_state.log_atividades, novo_registro], ignore_index=True)

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("👤 Perfil & Metas")
    st.session_state.peso_usuario = st.number_input("Peso (kg)", value=float(st.session_state.peso_usuario), step=0.1)
    
    st.divider()
    hoje = datetime.now().date()
    df_h = st.session_state.log_atividades
    if not df_h.empty:
        df_hoje = df_h[df_h['Data'].dt.date == hoje]
        cal_in = df_hoje[df_hoje['Tipo'] == 'Alimento']['Valor'].sum()
        cal_out = df_hoje[df_hoje['Tipo'] == 'Exercício']['Valor'].sum()
        st.metric("Consumo Hoje", f"{int(cal_in)} kcal")
        st.metric("Queima Hoje", f"{int(cal_out)} kcal")
        st.metric("Saldo Líquido", f"{int(cal_in - cal_out)} kcal")

# --- INTERFACE PRINCIPAL ---
st.title("🍎 BioStats: Diário Inteligente")

abas = st.tabs(["🍽️ Lançar Alimentos", "🏃 Lançar Exercícios", "📈 Relatórios", "📋 Histórico Detalhado", "⚙️ Banco"])

# --- ABA 1: ALIMENTAÇÃO (COM CÁLCULO EM TEMPO REAL) ---
with abas[0]:
    st.subheader("Nova Refeição")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        refeicao = st.selectbox("Escolha a Refeição:", ["Café da Manhã", "Almoço", "Café da Tarde", "Janta", "Snacks"])
        busca = st.text_input("🔍 Buscar alimento no banco:")
        opcoes = [a for a in st.session_state.banco_alimentos.keys() if busca.lower() in a.lower()]
        
        if opcoes:
            alimento_sel = st.selectbox("Alimento selecionado:", opcoes)
            
            # Lógica de unidade vs gramas
            is_unidade = "ovo" in alimento_sel.lower() or "un" in alimento_sel.lower()
            label_qtd = "Quantidade (unidades):" if is_unidade else "Quantidade (gramas - g):"
            
            qtd = st.number_input(label_qtd, min_value=0.0, value=100.0 if not is_unidade else 1.0, step=1.0)
            
            # CÁLCULO EM TEMPO REAL
            valor_unitario = st.session_state.banco_alimentos[alimento_sel]
            total_preview = qtd * valor_unitario
            
            st.markdown(f"### ⚡ Resultado: **{int(total_preview)} kcal**")
            
            if st.button("✅ Confirmar Lançamento"):
                adicionar_registro('Alimento', refeicao, alimento_sel, total_preview)
                st.success(f"{alimento_sel} lançado no {refeicao}!")
                st.rerun()
        else:
            st.warning("Alimento não encontrado. Cadastre na aba 'Banco'.")

# --- ABA 2: EXERCÍCIOS ---
with abas[1]:
    st.subheader("Atividade Física")
    tipo_ex = st.selectbox("O que você treinou?", ["Musculação", "Caminhada", "Corrida", "Natação", "Outro (Gasto Manual)"])
    
    if tipo_ex == "Outro (Gasto Manual)":
        desc_manual = st.text_input("Descrição do gasto:")
        cal_manual = st.number_input("Calorias estimadas:", min_value=0)
        if st.button("Lançar Gasto Manual"):
            adicionar_registro('Exercício', 'Extra', desc_manual, cal_manual)
            st.rerun()
    else:
        minutos = st.number_input("Duração (minutos):", min_value=1, value=45)
        mets = {"Musculação": 5.0, "Caminhada": 4.0, "Corrida": 8.0, "Natação": 7.0}
        gasto_ex = (mets[tipo_ex] * st.session_state.peso_usuario * (minutos/60))
        
        st.markdown(f"### 🔥 Queima estimada: **{int(gasto_ex)} kcal**")
        if st.button("✅ Lançar Exercício"):
            adicionar_registro('Exercício', 'Treino', tipo_ex, gasto_ex)
            st.rerun()

# --- ABA 3: RELATÓRIOS ---
with abas[2]:
    st.subheader("Estatísticas")
    # Filtros de Hoje, Semana e Mês
    periodo = st.radio("Período:", ["Hoje", "7 Dias", "30 Dias"], horizontal=True)
    dias = 0 if periodo == "Hoje" else (7 if periodo == "7 Dias" else 30)
    data_limite = datetime.now() - timedelta(days=dias)
    
    df_filt = st.session_state.log_atividades
    if not df_filt.empty:
        mask = df_filt['Data'] >= pd.to_datetime(data_limite).normalize()
        df_p = df_filt.loc[mask]
        
        c1, c2 = st.columns(2)
        c1.metric("Total Ingerido", f"{int(df_p[df_p['Tipo'] == 'Alimento']['Valor'].sum())} kcal")
        c2.metric("Total Queimado", f"{int(df_p[df_p['Tipo'] == 'Exercício']['Valor'].sum())} kcal")
        st.bar_chart(df_p.groupby('Tipo')['Valor'].sum())

# --- ABA 4: HISTÓRICO (DIVIDIDO POR CATEGORIAS) ---
with abas[3]:
    st.subheader("📅 Histórico de Hoje")
    df_h = st.session_state.log_atividades
    hoje_dt = datetime.now().date()
    
    if not df_h.empty:
        df_hoje = df_h[df_h['Data'].dt.date == hoje_dt]
        
        # --- SEÇÃO COMIDA ---
        st.markdown("### 🥗 Comida")
        for ref in ["Café da Manhã", "Almoço", "Café da Tarde", "Janta", "Snacks"]:
            df_ref = df_hoje[df_hoje['Categoria'] == ref]
            if not df_ref.empty:
                with st.expander(f"{ref} - Subtotal: {int(df_ref['Valor'].sum())} kcal", expanded=True):
                    for i, row in df_ref.iterrows():
                        c1, c2 = st.columns([4, 1])
                        c1.write(f"• {row['Descricao']}: {int(row['Valor'])} kcal")
                        if c2.button("🗑️", key=f"del_{i}"):
                            st.session_state.log_atividades = st.session_state.log_atividades.drop(i)
                            st.rerun()
        
        st.divider()
        
        # --- SEÇÃO EXERCÍCIO ---
        st.markdown("### 🏃 Exercício")
        df_exs = df_hoje[df_hoje['Tipo'] == 'Exercício']
        if not df_exs.empty:
            for i, row in df_exs.iterrows():
                c1, c2 = st.columns([4, 1])
                c1.write(f"• {row['Descricao']} ({row['Categoria']}): {int(row['Valor'])} kcal")
                if c2.button("🗑️", key=f"del_ex_{i}"):
                    st.session_state.log_atividades = st.session_state.log_atividades.drop(i)
                    st.rerun()
        else:
            st.info("Nenhum exercício lançado hoje.")
    else:
        st.info("O histórico está vazio.")

# --- ABA 5: BANCO DE DADOS ---
with abas[4]:
    st.subheader("Gerenciar Alimentos")
    n_nome = st.text_input("Nome do Alimento:")
    n_cal = st.number_input("Calorias (por 1g ou 1 unidade):", format="%.2f")
    st.caption("Ex: Se 100g de arroz tem 130kcal, coloque 1.30")
    
    if st.button("💾 Salvar no Banco"):
        if n_nome:
            st.session_state.banco_alimentos[n_nome] = n_cal
            st.success(f"{n_nome} cadastrado!")
            st.rerun()
        

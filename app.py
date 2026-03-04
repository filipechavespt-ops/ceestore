import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import sqlite3
from datetime import datetime

st.set_page_config(page_title="Sistema de Gestão", layout="wide")
conn = sqlite3.connect('gestao.db', check_same_thread=False)
c = conn.cursor()

def init_db():
    c.execute('''CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY, nome TEXT, preco REAL, qtd INTEGER, min INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS vendas (id INTEGER PRIMARY KEY, produto_id INTEGER, cliente TEXT, qtd INTEGER, total REAL, data TEXT)''')
    
    try:
        c.execute('ALTER TABLE vendas ADD COLUMN vendedor TEXT')
        c.execute("UPDATE vendas SET vendedor = cliente WHERE vendedor IS NULL")
    except sqlite3.OperationalError:
        pass
    conn.commit()

init_db()

# Atualização dos Usuários
names = ["Filipe", "Anderson", "Sabrina", "Breno", "Talles"]
usernames = ["filipe", "anderson", "sabrina", "breno", "talles"]
passwords = ["admin123", "admin456", "user123", "user456", "user789"]

hashed_passwords = stauth.Hasher(passwords).generate()
credentials = {"usernames": {}}
for i in range(len(usernames)):
    credentials["usernames"][usernames[i]] = {"name": names[i], "password": hashed_passwords[i], "role": "admin" if usernames[i] in ["filipe", "anderson"] else "user"}

authenticator = stauth.Authenticate(credentials, "gestao_cookie", "auth_key", cookie_expiry_days=30)
name, auth_status, username = authenticator.login('Login', 'main')

if auth_status:
    role = credentials["usernames"][username]["role"]
    st.sidebar.title(f"Bem-vindo, {name}")
    authenticator.logout('Sair', 'sidebar')
    menu = st.sidebar.radio("Navegação", ["📊 Dashboard", "📦 Estoque", "💰 Vendas"])

    if menu == "📦 Estoque":
        st.header("Gerenciamento de Estoque")
        if role == "admin":
            with st.expander("Cadastrar Novo Produto"):
                with st.form("form_prod"):
                    n = st.text_input("Nome")
                    p = st.number_input("Preço", min_value=0.0)
                    q = st.number_input("Qtd Inicial", min_value=0)
                    m = st.number_input("Alerta Mínimo", min_value=1)
                    if st.form_submit_button("Salvar"):
                        c.execute("INSERT INTO produtos (nome, preco, qtd, min) VALUES (?,?,?,?)", (n, p, q, m))
                        conn.commit()
                        st.success("Produto cadastrado!")
        df_p = pd.read_sql("SELECT * FROM produtos", conn)
        baixo = df_p[df_p['qtd'] <= df_p['min']]
        if not baixo.empty: st.error(f"⚠️ {len(baixo)} itens com estoque baixo!")
        st.dataframe(df_p, use_container_width=True)

    elif menu == "💰 Vendas":
        st.header("Registrar Venda")
        df_p = pd.read_sql("SELECT * FROM produtos", conn)
        with st.form("form_venda"):
            prod_nome = st.selectbox("Produto", df_p['nome'].tolist())
            qtd_v = st.number_input("Quantidade", min_value=1)
            # Alterado de Cliente para Colaborador na UI
            colaborador_v = st.text_input("Nome do Colaborador (Comprador)")
            if st.form_submit_button("Finalizar Venda"):
                if not colaborador_v.strip():
                    st.error("Informe o nome do colaborador.")
                else:
                    p_row = df_p[df_p['nome'] == prod_nome].iloc[0]
                    if p_row['qtd'] >= qtd_v:
                        total, data_v = p_row['preco'] * qtd_v, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        c.execute("INSERT INTO vendas (produto_id, cliente, vendedor, qtd, total, data) VALUES (?,?,?,?,?,?)", (int(p_row['id']), colaborador_v, name, qtd_v, total, data_v))
                        c.execute("UPDATE produtos SET qtd = qtd - ? WHERE id = ?", (qtd_v, int(p_row['id'])))
                        conn.commit()
                        st.success(f"Venda de R$ {total:.2f} registrada!")
                    else:
                        st.error("Estoque insuficiente!")

    elif menu == "📊 Dashboard":
        st.header("Visão Geral da Empresa" if role == "admin" else "Meu Desempenho")
        # Alias SQL para exibir 'colaborador' em vez de 'cliente'
        query = "SELECT v.*, p.nome as prod_nome, v.cliente as colaborador FROM vendas v JOIN produtos p ON v.produto_id = p.id"
        df_v = pd.read_sql(query, conn)
        
        if role == "user" and not df_v.empty:
            df_v = df_v[df_v['vendedor'] == name]

        if not df_v.empty:
            df_v['data'] = pd.to_datetime(df_v['data'])
            d_inicio, d_fim = st.date_input("Período", [df_v['data'].min().date(), df_v['data'].max().date()])
            df_f = df_v[(df_v['data'].dt.date >= d_inicio) & (df_v['data'].dt.date <= d_fim)]

            if not df_f.empty:
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Vendido", f"R$ {df_f['total'].sum():.2f}")
                col2.metric("Produto +Vendido", df_f.groupby('prod_nome')['qtd'].sum().idxmax())
                col3.metric("Melhor Vendedor", df_f.groupby('vendedor')['total'].sum().idxmax())
                
                st.divider()
                
                c_graf1, c_graf2 = st.columns(2)
                with c_graf1:
                    st.write("**Vendas por Dia (R$)**")
                    st.line_chart(df_f.groupby(df_f['data'].dt.date)['total'].sum(), height=250)
                with c_graf2:
                    st.write("**Qtd por Produto**")
                    st.bar_chart(df_f.groupby('prod_nome')['qtd'].sum(), height=250)

                st.divider()
                st.subheader("Detalhamento Diário")
                df_f['Data (Dia)'] = df_f['data'].dt.date
                resumo = df_f.groupby(['Data (Dia)', 'vendedor', 'prod_nome']).agg({'qtd': 'sum', 'total': 'sum'}).reset_index()
                resumo.columns = ['Data', 'Vendedor', 'Produto', 'Qtd Vendida', 'Total Arrecadado (R$)']
                st.dataframe(resumo, hide_index=True, use_container_width=True)

                if role == "admin":
                    st.divider()
                    st.subheader("🏆 Ranking de Vendedores")
                    rank_vendedor = df_f.groupby('vendedor').agg({'qtd': 'sum', 'total': 'sum'}).reset_index()
                    rank_vendedor.columns = ['Vendedor', 'Total de Itens Vendidos', 'Faturamento (R$)']
                    rank_vendedor = rank_vendedor.sort_values(by='Faturamento (R$)', ascending=False)
                    st.dataframe(rank_vendedor, hide_index=True, use_container_width=True)

                    st.divider()
                    st.subheader("🛠️ Log Completo de Transações")
                    log_completo = df_f[['data', 'vendedor', 'colaborador', 'prod_nome', 'qtd', 'total']].sort_values(by='data', ascending=False)
                    log_completo.columns = ['Data/Hora', 'Vendedor', 'Colaborador (Comprador)', 'Produto', 'Qtd', 'Total (R$)']
                    st.dataframe(log_completo, hide_index=True, use_container_width=True)

            else:
                st.info("Nenhuma venda no período selecionado.")
        else:
            st.warning("📊 Nenhuma venda registrada.")

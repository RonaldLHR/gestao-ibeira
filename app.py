import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import date

# --- 1. CONFIGURAÇÃO DO BANCO DE DADOS (MELHORADA) ---
# Usamos cache_resource para o engine não ser recriado a cada interação
@st.cache_resource
def get_engine():
    return create_engine('sqlite:///gestao_cursos.db', connect_args={"check_same_thread": False})

engine = get_engine()
Base = declarative_base()

class Solicitacao(Base):
    __tablename__ = 'solicitacoes'
    id = Column(Integer, primary_key=True)
    cliente = Column(String)
    solicitante = Column(String)
    curso = Column(String)
    modalidade = Column(String)
    horas = Column(Integer)
    fecha = Column(Date)
    coordinadora = Column(String)
    estado = Column(String)

Base.metadata.create_all(engine)
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

# --- 2. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestão Ibeira", layout="wide", page_icon="📋")

# CSS customizado para melhorar o visual
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; }
    </style>
    """, unsafe_allow_html=True)

st.title("📋 Gestão de Solicitações")

# --- 3. FORMULÁRIO LATERAL (CREATE) ---
with st.sidebar:
    st.header("➕ Nova Solicitação")
    with st.form("form_registro", clear_on_submit=True):
        f_cliente = st.text_input("Cliente")
        f_solicitante = st.text_input("Solicitante")
        f_curso = st.text_input("Curso")
        f_modalidade = st.selectbox("Modalidade", ["Presencial", "Online", "Híbrida"])
        f_horas = st.number_input("Horas", min_value=1, step=1)
        f_fecha = st.date_input("Fecha", value=date.today())
        f_coordinadora = st.selectbox("Coordinadora", ["Cristina Rodríguez", "Navas", "Yolanda"])
        f_estado = st.selectbox("Estado", ["recepcionada", "en gestão inicial", "en marcha", "cerrada/realizada"])
        
        submit = st.form_submit_button("Salvar no Banco", type="primary")
        
        if submit:
            if f_cliente and f_curso:
                with Session() as session:
                    nova = Solicitacao(cliente=f_cliente, solicitante=f_solicitante, curso=f_curso,
                                       modalidade=f_modalidade, horas=f_horas, fecha=f_fecha,
                                       coordinadora=f_coordinadora, estado=f_estado)
                    session.add(nova)
                    session.commit()
                st.success("✅ Adicionado com sucesso!")
                st.rerun()
            else:
                st.error("Preencha os campos obrigatórios (Cliente e Curso).")

# --- 4. FILTROS DE BUSCA (NOVIDADE) ---
with st.expander("🔍 Filtros e Busca", expanded=False):
    col1, col2, col3 = st.columns(3)
    with col1:
        busca_cliente = st.text_input("Filtrar por Cliente")
    with col2:
        busca_estado = st.multiselect("Filtrar por Estado", ["recepcionada", "en gestão inicial", "en marcha", "cerrada/realizada"])
    with col3:
        busca_coord = st.multiselect("Filtrar por Coordinadora", ["Cristina Rodríguez", "Navas", "Yolanda"])

# --- 5. ÁREA DE GESTÃO (READ, UPDATE, DELETE) ---
with Session() as session:
    query_obj = session.query(Solicitacao)
    
    # Aplicando Filtros se existirem
    if busca_cliente:
        query_obj = query_obj.filter(Solicitacao.cliente.ilike(f"%{busca_cliente}%"))
    if busca_estado:
        query_obj = query_obj.filter(Solicitacao.estado.in_(busca_estado))
    if busca_coord:
        query_obj = query_obj.filter(Solicitacao.coordinadora.in_(busca_coord))
    
    query = query_obj.all()

if query:
    data = [{
        "ID": s.id, "Excluir": False, "Cliente": s.cliente, "Solicitante": s.solicitante, 
        "Curso": s.curso, "Modalidade": s.modalidade, "Horas": s.horas, 
        "Data": s.fecha, "Coordinadora": s.coordinadora, "Estado": s.estado
    } for s in query]
    df = pd.DataFrame(data)

    st.info("💡 Edite as células abaixo e clique em 'Aplicar Alterações'. Marque 'Excluir' para remover registros.")

    # Tabela Editável com Configurações Visuais (Cores e Checkbox)
    edited_df = st.data_editor(
        df,
        column_config={
            "Excluir": st.column_config.CheckboxColumn("🗑️", default=False, help="Marque para deletar"),
            "ID": st.column_config.NumberColumn(disabled=True),
            "Estado": st.column_config.SelectboxColumn(
                options=["recepcionada", "en gestão inicial", "en marcha", "cerrada/realizada"],
                required=True
            ),
            "Horas": st.column_config.NumberColumn(format="%d h"),
            "Data": st.column_config.DateColumn(format="DD/MM/YYYY")
        },
        use_container_width=True,
        hide_index=True,
        key="editor_principal"
    )

    if st.button("💾 Aplicar Alterações no Banco", type="primary"):
        with Session() as session:
            for index, row in edited_df.iterrows():
                id_registro = int(row["ID"])
                registro_db = session.query(Solicitacao).filter(Solicitacao.id == id_registro).first()
                
                if row["Excluir"]:
                    session.delete(registro_db)
                else:
                    # Atualização em lote
                    registro_db.cliente = row["Cliente"]
                    registro_db.solicitante = row["Solicitante"]
                    registro_db.curso = row["Curso"]
                    registro_db.modalidade = row["Modalidade"]
                    registro_db.horas = row["Horas"]
                    registro_db.fecha = row["Data"]
                    registro_db.coordinadora = row["Coordinadora"]
                    registro_db.estado = row["Estado"]
            
            session.commit()
        st.success("🚀 Banco de dados atualizado com sucesso!")
        st.rerun()
else:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import date

# --- 1. CONFIGURACIÓN DE LA BASE DE DATOS ---
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
    modalidad = Column(String) #
    horas = Column(Integer)
    fecha_inicio = Column(Date) #
    fecha_fin = Column(Date)    #
    coordinadora = Column(String) #
    estado = Column(String) #

Base.metadata.create_all(engine)
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

# --- 2. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="gcformacion", layout="wide", page_icon="📋")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; }
    </style>
    """, unsafe_allow_html=True)

st.title("📋 Gestión de Solicitudes")

# --- 3. FORMULARIO LATERAL (CREATE) ---
with st.sidebar:
    st.header("➕ Nueva Solicitud")
    with st.form("form_registro", clear_on_submit=True):
        f_cliente = st.text_input("Cliente")
        f_solicitante = st.text_input("Solicitante")
        f_curso = st.text_input("Curso")
        
        # Opciones según la imagen
        f_modalidad = st.selectbox("Modalidad", [
            "Teleformación", "Presencial", "Presencial Aula Virtual", "Mixta", "Mixta Aula Virtual"
        ])
        
        f_horas = st.number_input("Horas", min_value=1, step=1)
        f_fecha_ini = st.date_input("Fecha Inicio", value=date.today())
        f_fecha_fin = st.date_input("Fecha Fin", value=date.today())
        
        # Coordinadoras según la imagen
        f_coordinadora = st.selectbox("Coordinadora", [
            "Cristina Rodríguez", "Cristina Navas", "Yolanda Sedeño"
        ])
        
        # Estados según la imagen
        f_estado = st.selectbox("Estado", [
            "Recepcionada", "En Gestión Inicial", "En Marcha", "Realizada"
        ])
        
        submit = st.form_submit_button("Guardar en Base de Datos", type="primary")
        
        if submit:
            if f_cliente and f_curso:
                session = Session()
                try:
                    nueva = Solicitacao(
                        cliente=f_cliente, solicitante=f_solicitante, curso=f_curso,
                        modalidad=f_modalidad, horas=f_horas, 
                        fecha_inicio=f_fecha_ini, fecha_fin=f_fecha_fin,
                        coordinadora=f_coordinadora, estado=f_estado
                    )
                    session.add(nueva)
                    session.commit()
                    st.success("✅ ¡Añadido con éxito!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    Session.remove()
            else:
                st.error("Por favor, rellene los campos obligatorios (Cliente y Curso).")

# --- 4. FILTROS DE BÚSQUEDA ---
with st.expander("🔍 Filtros y Búsqueda", expanded=False):
    col1, col2, col3 = st.columns(3)
    with col1:
        busca_cliente = st.text_input("Filtrar por Cliente")
    with col2:
        busca_estado = st.multiselect("Filtrar por Estado", ["Recepcionada", "En Gestión Inicial", "En Marcha", "Realizada"])
    with col3:
        busca_coord = st.multiselect("Filtrar por Coordinadora", ["Cristina Rodríguez", "Cristina Navas", "Yolanda Sedeño"])

# --- 5. ÁREA DE GESTIÓN (READ, UPDATE, DELETE) ---
session = Session()
query_obj = session.query(Solicitacao)

if busca_cliente:
    query_obj = query_obj.filter(Solicitacao.cliente.ilike(f"%{busca_cliente}%"))
if busca_estado:
    query_obj = query_obj.filter(Solicitacao.estado.in_(busca_estado))
if busca_coord:
    query_obj = query_obj.filter(Solicitacao.coordinadora.in_(busca_coord))

query = query_obj.all()

if query:
    data = [{
        "ID": s.id, 
        "Eliminar": False, 
        "Cliente": s.cliente, 
        "Solicitante": s.solicitante, 
        "Curso": s.curso, 
        "Modalidad": s.modalidad, 
        "Horas": s.horas, 
        "Fecha Inicio": s.fecha_inicio, 
        "Fecha Fin": s.fecha_fin,
        "Coordinadora": s.coordinadora, 
        "Estado": s.estado
    } for s in query]
    df = pd.DataFrame(data)

    st.info("💡 Edite las celdas y haga clic en 'Aplicar Cambios'. Marque 'Eliminar' para borrar registros.")

    edited_df = st.data_editor(
        df,
        column_config={
            "Eliminar": st.column_config.CheckboxColumn("🗑️", default=False),
            "ID": st.column_config.NumberColumn(disabled=True),
            "Modalidad": st.column_config.SelectboxColumn(
                options=["Teleformación", "Presencial", "Presencial Aula Virtual", "Mixta", "Mixta Aula Virtual"]
            ),
            "Estado": st.column_config.SelectboxColumn(
                options=["Recepcionada", "En Gestión Inicial", "En Marcha", "Realizada"],
                required=True
            ),
            "Coordinadora": st.column_config.SelectboxColumn(
                options=["Cristina Rodríguez", "Cristina Navas", "Yolanda Sedeño"]
            ),
            "Horas": st.column_config.NumberColumn(format="%d h"),
            "Fecha Inicio": st.column_config.DateColumn(format="DD/MM/YYYY"),
            "Fecha Fin": st.column_config.DateColumn(format="DD/MM/YYYY")
        },
        use_container_width=True,
        hide_index=True,
        key="editor_principal"
    )

    if st.button("💾 Aplicar Cambios en la Base de Datos", type="primary"):
        try:
            for index, row in edited_df.iterrows():
                id_reg = int(row["ID"])
                reg_db = session.query(Solicitacao).filter(Solicitacao.id == id_reg).first()
                
                if row["Eliminar"]:
                    session.delete(reg_db)
                else:
                    reg_db.cliente = row["Cliente"]
                    reg_db.solicitante = row["Solicitante"]
                    reg_db.curso = row["Curso"]
                    reg_db.modalidad = row["Modalidad"]
                    reg_db.horas = row["Horas"]
                    reg_db.fecha_inicio = row["Fecha Inicio"]
                    reg_db.fecha_fin = row["Fecha Fin"]
                    reg_db.coordinadora = row["Coordinadora"]
                    reg_db.estado = row["Estado"]
            
            session.commit()
            st.success("🚀 ¡Base de datos actualizada!")
            st.rerun()
        except Exception as e:
            st.error(f"Error al actualizar: {e}")
            session.rollback()
        finally:
            Session.remove()
else:
    st.warning("No se encontraron datos.")
    Session.remove()
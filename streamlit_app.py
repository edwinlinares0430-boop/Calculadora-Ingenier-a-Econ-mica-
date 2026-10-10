# -*- coding: utf-8 -*-
import streamlit as st
import calculator_engine as eng

st.set_page_config(
    page_title="Calculadora de Ingeniería Económica",
    page_icon="📈",
    layout="wide",
)

st.markdown("""
<style>
.block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
.small-note {color:#6b7280; font-size:0.9rem;}
.result-box {
    border:1px solid rgba(128,128,128,.25);
    border-radius:12px;
    padding:1rem 1.1rem;
    background:rgba(128,128,128,.04);
}
div[data-testid="stTextArea"] textarea {font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;}
</style>
""", unsafe_allow_html=True)

st.title("Calculadora de Ingeniería Económica")
st.caption(
    "Interés compuesto · Conversión de tasas · Tasas indexadas · "
    "Anualidades · Perpetuidades · Resolver ejercicio"
)

def show_result(texto):
    st.markdown("#### Resultado y procedimiento")
    st.code(texto, language=None)

def safe_float(label, value=0.0, key=None, min_value=None):
    return st.number_input(label, value=float(value), key=key, min_value=min_value)

def rate_inputs(prefix, per_objetivo="Mensual"):
    c1,c2,c3 = st.columns(3)
    with c1:
        valor = st.number_input("Tasa (%)", value=10.0, key=f"{prefix}_rate")
    with c2:
        tipo = st.selectbox("Tipo de tasa", eng.TIPOS_TASA, key=f"{prefix}_tipo")
    with c3:
        per = st.selectbox("Periodicidad de la tasa", list(eng.PERIODOS), key=f"{prefix}_per")
    i, pasos = eng.normalizar_tasa(valor, tipo, per, per_objetivo)
    return valor, tipo, per, i, pasos

tabs = st.tabs([
    "Resolver ejercicio",
    "Interés compuesto",
    "Conversión de tasas",
    "Tasas indexadas",
    "Anualidad vencida",
    "Anualidad anticipada",
    "Perpetuidades",
    "Integradores",
])

# ============================================================
# RESOLVER EJERCICIO
# ============================================================
with tabs[0]:
    st.subheader("Resolver ejercicio")
    st.write(
        "Pegue el enunciado completo. La calculadora intenta identificar automáticamente "
        "el tipo de problema, los datos, las tasas, los periodos y la incógnita."
    )

    validaciones = ["— Seleccionar —"] + list(eng.VALIDACIONES_PROYECTO.keys())
    seleccion = st.selectbox("Ejercicio de validación (opcional)", validaciones)

    if "resolver_texto" not in st.session_state:
        st.session_state.resolver_texto = ""

    if seleccion != "— Seleccionar —":
        if st.button("Cargar ejercicio seleccionado"):
            st.session_state.resolver_texto = eng.VALIDACIONES_PROYECTO[seleccion]

    texto = st.text_area(
        "Enunciado",
        key="resolver_texto",
        height=240,
        placeholder="Pegue aquí el ejercicio completo..."
    )

    c1,c2,c3 = st.columns([1,1,4])
    analizar = c1.button("Analizar", type="primary")
    resolver = c2.button("Resolver")

    if analizar or resolver:
        if not texto.strip():
            st.warning("Pegue primero un ejercicio.")
        else:
            try:
                a = eng.analizar_ejercicio_texto(texto)
                st.markdown("#### Identificación automática")
                st.code(eng.resumen_analisis(a), language=None)
                if resolver:
                    show_result(eng.resolver_analisis(a))
            except Exception as e:
                st.error(str(e))

    st.info(
        "El analizador reconoce también cantidades escritas en palabras, por ejemplo: "
        "“cinco años”, “sesenta meses”, “treinta y seis pagos” y “pago número veinte”."
    )

# ============================================================
# INTERÉS COMPUESTO
# ============================================================
with tabs[1]:
    st.subheader("Interés compuesto")
    op = st.selectbox("¿Qué desea calcular?", ["Valor futuro","Valor presente","Tasa","Tiempo"])
    c1,c2 = st.columns(2)
    P = F = n = None

    if op != "Valor presente":
        P = c1.number_input("Valor presente P", value=100000000.0, min_value=0.0)
    if op != "Valor futuro":
        F = c2.number_input("Valor futuro F", value=150000000.0, min_value=0.0)

    if op != "Tiempo":
        n = st.number_input("Número de periodos n", value=12.0, min_value=0.0)

    if op != "Tasa":
        per_obj = st.selectbox("Periodicidad del tiempo", list(eng.PERIODOS), index=5)
        _,_,_,i,pasos = rate_inputs("ic", per_obj)
    else:
        per_obj = st.selectbox("Periodicidad de la tasa buscada", list(eng.PERIODOS), index=5)
        pasos = ""

    if st.button("Calcular interés compuesto"):
        try:
            if op == "Valor futuro":
                r = eng.ic_vf(P,i,n)
                show_result(f"F = {eng.fmt_moneda(r)}\n\n{pasos}")
            elif op == "Valor presente":
                r = eng.ic_vp(F,i,n)
                show_result(f"P = {eng.fmt_moneda(r)}\n\n{pasos}")
            elif op == "Tasa":
                r = eng.ic_tasa(P,F,n)
                show_result(f"i = {eng.fmt_tasa(r)} por periodo.")
            else:
                r = eng.ic_n(P,F,i)
                show_result(f"n = {r:.6f} periodos.\n\n{pasos}")
        except Exception as e:
            st.error(str(e))

# ============================================================
# CONVERSIÓN DE TASAS
# ============================================================
with tabs[2]:
    st.subheader("Conversión de tasas")
    c1,c2,c3,c4 = st.columns(4)
    valor = c1.number_input("Tasa de entrada (%)", value=12.0)
    tipo = c2.selectbox("Tipo de entrada", eng.TIPOS_TASA)
    per_origen = c3.selectbox("Periodicidad de entrada", list(eng.PERIODOS))
    salida = c4.selectbox(
        "Salida",
        ["Periódica vencida","Periódica anticipada","Efectiva anual",
         "Nominal anual vencida","Nominal anual anticipada"]
    )
    per_dest = st.selectbox("Periodicidad de salida", list(eng.PERIODOS), index=5)

    if st.button("Convertir tasa"):
        try:
            iv, pasos = eng.normalizar_tasa(valor,tipo,per_origen,per_dest)
            ea = eng.periodica_a_ea(iv, eng.PERIODOS[per_dest])
            if salida == "Periódica vencida":
                res = iv
            elif salida == "Periódica anticipada":
                res = eng.vencida_a_anticipada(iv)
            elif salida == "Efectiva anual":
                res = ea
            elif salida == "Nominal anual vencida":
                res = iv * eng.PERIODOS[per_dest]
            else:
                res = eng.vencida_a_anticipada(iv) * eng.PERIODOS[per_dest]
            show_result(f"Resultado = {eng.fmt_tasa(res)}\n\n{pasos}")
        except Exception as e:
            st.error(str(e))

# ============================================================
# TASAS INDEXADAS
# ============================================================
with tabs[3]:
    st.subheader("Tasas indexadas")
    indice = st.selectbox("Índice", ["IPC","IBR","DTF","UVR"])
    c1,c2 = st.columns(2)
    base = c1.number_input("Índice / tasa base (%)", value=5.0)
    margen = c2.number_input("Margen / tasa adicional (%)", value=4.0)
    salida_per = st.selectbox("Periodicidad de salida", list(eng.PERIODOS), index=5)

    modalidad = "EA"
    if indice == "DTF":
        modalidad = st.selectbox("Modalidad DTF", ["TA","NTA"])
    elif indice == "IBR":
        modalidad = st.selectbox("Modalidad IBR", ["EA","SV"])

    if st.button("Calcular tasa indexada"):
        try:
            if indice == "DTF":
                if modalidad == "NTA":
                    ia_base = eng.pct(base)/4
                else:
                    ia_base = eng.pct(base)
                ia_total = ia_base + eng.pct(margen)
                ivt = eng.anticipada_a_vencida(ia_total)
                ea = eng.periodica_a_ea(ivt,4)
                pasos = (
                    f"DTF TA compatible = {eng.fmt_tasa(ia_base)}\n"
                    f"DTF + margen TA = {eng.fmt_tasa(ia_total)}\n"
                    f"Trimestral vencida = {eng.fmt_tasa(ivt)}\n"
                    f"EA = {eng.fmt_tasa(ea)}"
                )
            elif indice == "IBR" and modalidad == "SV":
                margen_sv = eng.ea_a_periodica(eng.pct(margen),2)
                total_sv = (1+eng.pct(base))*(1+margen_sv)-1
                ea = eng.periodica_a_ea(total_sv,2)
                pasos = (
                    f"Margen SV = {eng.fmt_tasa(margen_sv)}\n"
                    f"Total SV = {eng.fmt_tasa(total_sv)}\n"
                    f"EA = {eng.fmt_tasa(ea)}"
                )
            else:
                ea = (1+eng.pct(base))*(1+eng.pct(margen))-1
                pasos = f"(1+i_base)(1+i_margen)-1 = {eng.fmt_tasa(ea)} EA"
            iout = eng.ea_a_periodica(ea, eng.PERIODOS[salida_per])
            show_result(
                f"Tasa efectiva anual = {eng.fmt_tasa(ea)}\n"
                f"Tasa {salida_per.lower()} vencida = {eng.fmt_tasa(iout)}\n\n{pasos}"
            )
        except Exception as e:
            st.error(str(e))

# ============================================================
# ANUALIDADES
# ============================================================
def annuity_tab(anticipada=False):
    titulo = "Anualidad anticipada" if anticipada else "Anualidad vencida"
    st.subheader(titulo)
    op = st.selectbox(
        "¿Qué desea calcular?",
        ["Cuota desde VP","Cuota desde VF","Valor presente","Valor futuro","Número de pagos desde VP","Número de pagos desde VF"],
        key=f"ann_op_{anticipada}"
    )
    per = st.selectbox("Periodicidad de los pagos", list(eng.PERIODOS), index=5, key=f"ann_per_{anticipada}")
    _,_,_,i,pasos = rate_inputs(f"ann_{anticipada}", per)

    c1,c2 = st.columns(2)
    A=P=F=n=None
    if op == "Cuota desde VP":
        P=c1.number_input("VP", value=500000000.0, min_value=0.0, key=f"vp1_{anticipada}")
        n=c2.number_input("n", value=36.0, min_value=0.0, key=f"n1_{anticipada}")
    elif op == "Cuota desde VF":
        F=c1.number_input("VF", value=800000000.0, min_value=0.0, key=f"vf2_{anticipada}")
        n=c2.number_input("n", value=36.0, min_value=0.0, key=f"n2_{anticipada}")
    elif op == "Valor presente":
        A=c1.number_input("A", value=15000000.0, min_value=0.0, key=f"a3_{anticipada}")
        n=c2.number_input("n", value=36.0, min_value=0.0, key=f"n3_{anticipada}")
    elif op == "Valor futuro":
        A=c1.number_input("A", value=15000000.0, min_value=0.0, key=f"a4_{anticipada}")
        n=c2.number_input("n", value=36.0, min_value=0.0, key=f"n4_{anticipada}")
    elif op == "Número de pagos desde VP":
        P=c1.number_input("VP", value=500000000.0, min_value=0.0, key=f"vp5_{anticipada}")
        A=c2.number_input("A", value=15000000.0, min_value=0.0, key=f"a5_{anticipada}")
    else:
        F=c1.number_input("VF", value=800000000.0, min_value=0.0, key=f"vf6_{anticipada}")
        A=c2.number_input("A", value=15000000.0, min_value=0.0, key=f"a6_{anticipada}")

    if st.button("Calcular", key=f"ann_btn_{anticipada}"):
        try:
            if anticipada:
                fvp,fvf,fcvp,fcvf,fnvp,fnvf = (
                    eng.aa_vp, eng.aa_vf, eng.aa_cuota_vp, eng.aa_cuota_vf, eng.aa_n_vp, eng.aa_n_vf
                )
            else:
                fvp,fvf,fcvp,fcvf,fnvp,fnvf = (
                    eng.av_vp, eng.av_vf, eng.av_cuota_vp, eng.av_cuota_vf, eng.av_n_vp, eng.av_n_vf
                )
            if op == "Cuota desde VP":
                res=f"A = {eng.fmt_moneda(fcvp(P,i,n))}"
            elif op == "Cuota desde VF":
                res=f"A = {eng.fmt_moneda(fcvf(F,i,n))}"
            elif op == "Valor presente":
                res=f"VP = {eng.fmt_moneda(fvp(A,i,n))}"
            elif op == "Valor futuro":
                res=f"VF = {eng.fmt_moneda(fvf(A,i,n))}"
            elif op == "Número de pagos desde VP":
                x=fnvp(P,A,i); res=f"n teórico = {x:.6f}\nn entero mínimo = {eng.math.ceil(x-1e-12)}"
            else:
                x=fnvf(F,A,i); res=f"n teórico = {x:.6f}\nn entero mínimo = {eng.math.ceil(x-1e-12)}"
            show_result(res+"\n\n"+pasos)
        except Exception as e:
            st.error(str(e))

with tabs[4]:
    annuity_tab(False)

with tabs[5]:
    annuity_tab(True)

# ============================================================
# PERPETUIDADES
# ============================================================
with tabs[6]:
    st.subheader("Perpetuidades")
    op = st.selectbox("¿Qué desea calcular?", ["Capital P","Pago A","Tasa i"])
    c1,c2 = st.columns(2)
    P=A=i=None
    if op != "Capital P":
        P=c1.number_input("Capital P", value=800000000.0, min_value=0.0)
    if op != "Pago A":
        A=c2.number_input("Pago perpetuo A", value=70000000.0, min_value=0.0)
    if op != "Tasa i":
        tasa=st.number_input("Tasa periódica (%)", value=8.5)
        i=eng.pct(tasa)

    if st.button("Calcular perpetuidad"):
        try:
            if op=="Capital P":
                res=eng.perp_capital(A,i); show_result(f"P = {eng.fmt_moneda(res)}")
            elif op=="Pago A":
                res=eng.perp_pago(P,i); show_result(f"A = {eng.fmt_moneda(res)}")
            else:
                res=eng.perp_tasa(P,A); show_result(f"i = {eng.fmt_tasa(res)}")
        except Exception as e:
            st.error(str(e))

# ============================================================
# INTEGRADORES
# ============================================================
with tabs[7]:
    st.subheader("Integradores")
    st.write(
        "Los problemas integradores combinan varios motores financieros. "
        "Para evitar pedir decenas de campos manuales, aquí se resuelven desde el enunciado completo."
    )
    integrador = st.text_area(
        "Pegue el caso integrador",
        height=300,
        placeholder="Ej.: varias fuentes, reserva final, transferencia entre fondos, equivalencia de planes..."
    )
    if st.button("Resolver caso integrador", type="primary"):
        if not integrador.strip():
            st.warning("Pegue primero un enunciado.")
        else:
            try:
                a=eng.analizar_ejercicio_texto(integrador)
                st.code(eng.resumen_analisis(a), language=None)
                show_result(eng.resolver_analisis(a))
            except Exception as e:
                st.error(str(e))

st.divider()
st.caption(
    "Calculadora desarrollada para Ingeniería Económica. "
    "Los resultados deben interpretarse con coherencia entre tasa, periodicidad y tiempo."
)

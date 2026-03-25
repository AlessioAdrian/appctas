import streamlit as st
import pytesseract
from PIL import Image
import pandas as pd
import re
from datetime import datetime
import os

# (Windows) se der erro de tesseract, descomente e ajuste o caminho:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

st.set_page_config(page_title="Gastos Automáticos", page_icon="💸", layout="centered")
st.title("Registro Automático de Gastos 💸")
st.caption("Tire foto da nota → eu leio o valor → salvo pra você")

arquivo_csv = "gastos.csv"

# Carrega gastos existentes
if os.path.exists(arquivo_csv):
    df = pd.read_csv(arquivo_csv)
else:
    df = pd.DataFrame(columns=["data", "descricao", "valor", "categoria"])

# --- UPLOAD E OCR ---
arquivo = st.file_uploader("📸 Foto do comprovante/nota", type=["jpg","png","jpeg"])

valor_detectado = "0.00"
data_detectada = datetime.now().strftime("%d/%m/%Y")
descricao_detectada = ""

if arquivo:
    img = Image.open(arquivo)
    st.image(img, caption="Comprovante", width=300)

    with st.spinner("Lendo nota fiscal..."):
        texto = pytesseract.image_to_string(img, lang='por')

    # Extrai VALOR (procura R$ 12,34 ou TOTAL 12.34)
    valores = re.findall(r'(?:R\$|TOTAL|VALOR|VALOR TOTAL)\s*([\d]{1,3}(?:\.\d{3})*,\d{2})', texto, re.IGNORECASE)
    if not valores:
        valores = re.findall(r'(\d+,\d{2})', texto)
    if valores:
        valor_detectado = valores[-1].replace('.','').replace(',','.') # pega o último (geralmente o total)

    # Extrai DATA
    datas = re.findall(r'(\d{2}/\d{2}/\d{4})', texto)
    if datas:
        data_detectada = datas[0]

    # Tenta pegar nome do estabelecimento
    linhas = [l.strip() for l in texto.split('\n') if len(l.strip()) > 3]
    if linhas:
        descricao_detectada = linhas[0][:30]

    with st.expander("Ver texto lido (pra conferir)"):
        st.text(texto)

# --- FORMULÁRIO ---
st.subheader("Confirme os dados")
col1, col2 = st.columns(2)
with col1:
    data = st.text_input("Data", value=data_detectada)
    valor = st.text_input("Valor (R$)", value=valor_detectado)
with col2:
    descricao = st.text_input("Estabelecimento", value=descricao_detectada)
    categoria = st.selectbox("Categoria", ["Alimentação", "Transporte", "Mercado", "Lazer", "Saúde", "Outros"])

col_a, col_b = st.columns(2)
with col_a:
    if st.button("💾 Salvar gasto", type="primary", use_container_width=True):
        try:
            novo = pd.DataFrame([{
                "data": data,
                "descricao": descricao,
                "valor": float(valor),
                "categoria": categoria
            }])
            df = pd.concat([df, novo], ignore_index=True)
            df.to_csv(arquivo_csv, index=False)
            st.success(f"Gasto de R$ {valor} salvo!")
            st.rerun()
        except:
            st.error("Verifique o valor (use ponto: 12.50)")
with col_b:
    if st.button("🗑️ Apagar último", use_container_width=True) and not df.empty:
        df = df.iloc[:-1]
        df.to_csv(arquivo_csv, index=False)
        st.warning("Último lançamento apagado")
        st.rerun()

# --- RELATÓRIO ---
if not df.empty:
    st.divider()
    st.subheader("Seus gastos")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total gasto", f"R$ {df['valor'].sum():.2f}")
    col2.metric("Lançamentos", len(df))
    col3.metric("Ticket médio", f"R$ {df['valor'].mean():.2f}")

    st.dataframe(df.sort_values(by="data", ascending=False), use_container_width=True)

    # Gráfico por categoria
    st.subheader("Gastos por categoria")
    grafico = df.groupby('categoria')['valor'].sum().sort_values(ascending=False)
    st.bar_chart(grafico)

    # Exportar
    st.download_button(
        "📥 Baixar Excel/CSV",
        df.to_csv(index=False).encode('utf-8'),
        "meus_gastos.csv",
        "text/csv",
        use_container_width=True
    )
else:
    st.info("Nenhum gasto registrado ainda. Envie a foto da primeira nota!")

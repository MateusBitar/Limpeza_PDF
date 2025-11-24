import streamlit as st
import pdfplumber
import io
import zipfile
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase import pdfmetrics
import unicodedata
import re

pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))

def normalize_text(text):
    return unicodedata.normalize("NFC", text)

def limpar_texto(texto):
    texto = normalize_text(texto)
    padrao_referencias = r"(REFERÊNCIAS|Referências)(.|\n)*"
    texto = re.sub(padrao_referencias, "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"http\S+|www\.\S+", "", texto)
    texto = re.sub(r"\S+@\S+\.\S+", "", texto)
    texto = re.sub(r"^\s*\d+\s*$", "", texto, flags=re.MULTILINE)
    linhas = texto.split("\n")
    linhas = [l for l in linhas if len(l.strip()) > 3]
    texto = "\n".join(linhas)
    texto = re.sub(r"\n\s*\n", "\n\n", texto)
    return texto.strip()

def salvar_pdf(texto):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    styles = getSampleStyleSheet()
    style = styles["Normal"]
    style.fontName = "HeiseiMin-W3"

    story = [Paragraph(line, style) for line in texto.split("\n")]
    doc.build(story)
    buffer.seek(0)
    return buffer

st.title("🧹 Limpeza de PDFs para LLM – Multi Arquivos")
st.write("Insira a baixo os PDFs a serem limpos.")

uploaded_files = st.file_uploader("Envie vários PDFs", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    pdfs_limpos = []

    for arquivo in uploaded_files:
        st.write(f"Processando: **{arquivo.name}**...")
        texto_extraido = ""
        with pdfplumber.open(arquivo) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    texto_extraido += text + "\n"

        texto_limpo = limpar_texto(texto_extraido)
        nome_saida = arquivo.name.replace(".pdf", "") + "_limpo.pdf"
        pdf_buffer = salvar_pdf(texto_limpo)

        pdfs_limpos.append((nome_saida, pdf_buffer))

        st.download_button(
            label=f"Baixar {nome_saida}",
            data=pdf_buffer,
            file_name=nome_saida,
            mime="application/pdf"
        )

    st.success("Todos os PDFs foram processados!")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for nome, buffer in pdfs_limpos:
            zipf.writestr(nome, buffer.getvalue())

    zip_buffer.seek(0)

    st.download_button(
        label="📦 Baixar todos os PDFs limpos (.zip)",
        data=zip_buffer,
        file_name="pdfs_limpos.zip",
        mime="application/zip"
    )

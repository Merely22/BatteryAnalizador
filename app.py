import streamlit as st
import pandas as pd
import re
from datetime import datetime
import io
from xlsxwriter import Workbook

def process_txt_file(file_content, filename):
    """
    Procesa el contenido de un archivo .txt para extraer el último mensaje GNBAT.
    """
    lines = file_content.decode("utf-8", errors="ignore").splitlines()
    gnbat_lines = [line for line in lines if "$GNBAT" in line]

    if not gnbat_lines:
        return None

    ultimo_gnbat = gnbat_lines[-1]
    match = re.search(r"(\d{2}:\d{2}:\d{2})\.\d+\s+\$GNBAT,(\d+),([\d\.]+)", ultimo_gnbat)

    if match:
        hora, bateria, voltaje = match.groups()
        mac = filename[-8:-4] # Extraer MAC del nombre del archivo

        # Extraer fecha del nombre del archivo (serial_YYYYMMDD_....)
        try:
            fecha_str = filename[7:15]
            fecha = datetime.strptime(fecha_str, "%Y%m%d").date()
        except ValueError:
            fecha = None # Si no se puede extraer, se deja como None

        return {
            "Fecha": fecha,
            "Hora": hora,
            "MAC": mac,
            "Bateria (%)": int(bateria),
            "Voltaje (V)": float(voltaje),
            "Archivo": filename
        }
    return None

st.set_page_config(page_title="Analizador de Batería GNBAT", layout="wide")

st.title("🔋Analizado de Batería")
st.markdown("Sube tus archivos `.txt` para extraer el último nivel de batería y voltaje.")

uploaded_files = st.file_uploader(
    "Sube tus archivos de texto aquí",
    type="txt",
    accept_multiple_files=True
)

if uploaded_files:
    st.write(f"📂 {len(uploaded_files)} archivo(s) seleccionados.")
    data_records = []
    processed_files_count = 0
    skipped_files_count = 0

    with st.spinner("Procesando archivos..."):
        for uploaded_file in uploaded_files:
            file_name = uploaded_file.name
            file_content = uploaded_file.read()
            
            result = process_txt_file(file_content, file_name)
            
            if result:
                data_records.append(result)
                processed_files_count += 1
            else:
                st.warning(f"⚠️ No se pudo extraer datos GNBAT de: {file_name}")
                skipped_files_count += 1

    if data_records:
        df = pd.DataFrame(data_records)
        df_sorted = df.sort_values(by="Fecha", ascending=False)

        st.success(f"✅ Se procesaron {processed_files_count} archivos exitosamente.")
        if skipped_files_count > 0:
            st.warning(f"❌ Se omitieron {skipped_files_count} archivos sin datos GNBAT válidos.")

        st.subheader("Resumen de Datos de Batería")
        st.dataframe(df_sorted)

        # Gráfico de barras simple para la batería
        st.subheader("Distribución de Niveles de Batería")
        st.bar_chart(df_sorted.set_index("MAC")["Bateria (%)"])
        
        # Descargar a Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_sorted.to_excel(writer, index=False, sheet_name='NivelesBateria')
        output.seek(0) # Rewind the buffer

        st.download_button(
            label="Descargar Datos a Excel",
            data=output.getvalue(),
            file_name="battery_analysis.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("❌ No se encontraron datos GNBAT válidos en los archivos subidos.")

st.markdown("---")
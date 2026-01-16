import os
import json
import pdfplumber
from config import GROQ_API_KEY, PDF_PASSWORD
from groq import Groq

def procesar_pdf(pdf_path: str, output_dir: str = "outputs") -> bool:
    """
    Procesa un PDF individual y lo convierte a JSON usando Groq AI.
    
    Args:
        pdf_path: Ruta al archivo PDF
        output_dir: Directorio de salida para JSON
    
    Returns:
        True si se procesó exitosamente, False en caso contrario
    """
    print(f"\n{'='*60}")
    print(f"📄 Procesando: {os.path.basename(pdf_path)}")
    print(f"{'='*60}")
    
    # 1. LEER EL PDF Y EXTRAER TEXTO
    try:
        with pdfplumber.open(pdf_path, password=PDF_PASSWORD) as pdf:
            leer_pdf_texto = ""
            for page in pdf.pages:
                texto_pagina = page.extract_text()
                if texto_pagina:
                    leer_pdf_texto += texto_pagina + "\n"
            
            print(f"  ✅ PDF leído: {len(leer_pdf_texto)} caracteres")
    except Exception as e:
        print(f"  ❌ Error leyendo PDF: {e}")
        return False

    # 2. ENVIAR A GROQ CON INSTRUCCIONES DE SISTEMA
    client = Groq(api_key=GROQ_API_KEY)
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """Eres un asistente experto en análisis de cartolas bancarias chilenas.
IMPORTANTE: Debes responder ÚNICAMENTE con un JSON válido, sin texto adicional ni explicaciones.
El JSON debe tener este formato exacto:
{
  "transacciones": [
    {
      "fecha": "YYYY-MM-DD",
      "descripcion": "texto descriptivo",
      "monto": numero_entero,
      "tipo": "ingreso" o "egreso"
    }
  ]
}

REGLAS:
- En Chile los montos usan punto como separador de miles (ej: 1.234.567 = un millón)
- No hay decimales en pesos chilenos
- "PAGO", "GIRO", "IMPUESTO", "TRASPASO A" = egreso
- "TRANSFERENCIA DESDE", "TRASPASO DE", "ABONO" = ingreso
- Ignora totales, resúmenes y headers
- Extrae TODAS las transacciones que encuentres"""
                },
                {
                    "role": "user",
                    "content": f"Extrae todas las transacciones de esta cartola:\n\n{leer_pdf_texto[:8000]}"
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.1
        )
        print(f"  🤖 IA procesó el documento")
    except Exception as e:
        print(f"  ❌ Error al llamar a Groq: {e}")
        return False

    # 3. PROCESAR RESPUESTA JSON
    respuesta = chat_completion.choices[0].message.content

    try:
        # Extraer JSON de la respuesta (por si viene con markdown)
        if "```json" in respuesta:
            inicio = respuesta.find("```json") + 7
            fin = respuesta.find("```", inicio)
            respuesta = respuesta[inicio:fin].strip()
        elif "```" in respuesta:
            inicio = respuesta.find("```") + 3
            fin = respuesta.find("```", inicio)
            respuesta = respuesta[inicio:fin].strip()
        
        # Parsear JSON
        datos = json.loads(respuesta)
        
        num_transacciones = len(datos.get('transacciones', []))
        print(f"  ✅ Extraídas: {num_transacciones} transacciones")
        
        # Calcular totales
        total_ingresos = sum(t['monto'] for t in datos['transacciones'] if t['tipo'] == 'ingreso')
        total_egresos = sum(t['monto'] for t in datos['transacciones'] if t['tipo'] == 'egreso')
        
        print(f"  💰 Ingresos: ${total_ingresos:,}")
        print(f"  💸 Egresos: ${total_egresos:,}")
        print(f"  📊 Balance: ${total_ingresos - total_egresos:,}")
        
        # Guardar JSON procesado
        os.makedirs(output_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}_procesado.json")
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        
        print(f"  💾 Guardado: {output_path}")
        return True
        
    except json.JSONDecodeError as e:
        print(f"  ❌ Error parseando JSON: {e}")
        print(f"  Respuesta recibida:\n{respuesta[:200]}...")
        return False


def procesar_todos_los_pdfs(input_dir: str = "downloads", output_dir: str = "outputs"):
    """
    Procesa todos los PDFs en un directorio.
    
    Args:
        input_dir: Directorio con PDFs a procesar
        output_dir: Directorio de salida para JSONs
    """
    print(f"\n🚀 Iniciando procesamiento de PDFs")
    print(f"📂 Entrada: {input_dir}/")
    print(f"📂 Salida: {output_dir}/\n")
    
    # Buscar todos los PDFs
    if not os.path.exists(input_dir):
        print(f"❌ El directorio {input_dir}/ no existe")
        return
    
    pdfs = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    
    if not pdfs:
        print(f"❌ No se encontraron PDFs en {input_dir}/")
        return
    
    print(f"📋 Encontrados: {len(pdfs)} PDF(s)\n")
    
    # Procesar cada PDF
    exitosos = 0
    fallidos = 0
    
    for pdf_file in pdfs:
        pdf_path = os.path.join(input_dir, pdf_file)
        
        if procesar_pdf(pdf_path, output_dir):
            exitosos += 1
        else:
            fallidos += 1
    
    # Resumen final
    print(f"\n{'='*60}")
    print(f"✅ Procesamiento completado")
    print(f"   Exitosos: {exitosos}/{len(pdfs)}")
    if fallidos > 0:
        print(f"   Fallidos: {fallidos}/{len(pdfs)}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    # Ejecutar procesamiento de todos los PDFs
    procesar_todos_los_pdfs()

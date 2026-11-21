# Asistente SOC con RAG — NovaCloud Corp

Prototipo de sistema **RAG (Retrieval-Augmented Generation)** para consultas sobre normativa de seguridad, playbooks de respuesta a incidentes, matriz de SLA/escalamiento, hardening de servidores e historial de incidentes.

## Estructura del proyecto

```text
Parcial2-SIC/
├── corpus/                          # 5 documentos sintéticos en 3 formatos (.pdf, .docx, .md)
│   ├── Guia_Hardening_Red_y_Servidores.pdf
│   ├── Matriz_SLA_y_Escalamiento.docx
│   ├── Playbook_Respuesta_Incidentes.md
│   ├── Politica_Seguridad_y_Accesos.pdf
│   └── Registro_Incidentes_Resueltos.md
├── docs/							# Enunciado del proyecto de RAG e Informe final
│	├── Enunciado_Proyecto_RAG.docx
│	└── Informe_Proyecto_RAG.docx
├── notebooks/
│   ├── rag_core.py                  # Módulo compartido (ingesta, chunking, denso/BM25, LLM)
│   ├── 01_Base_R0.ipynb             # Prototipo base R0 y pruebas de desarrollo
│   └── 02_Experimentos_y_Evaluacion.ipynb  # Variantes R1, R2, C0, R0_ALT y 45 corridas
├── resultados/
│   ├── resultados_corridas.json     # Registro completo de las 45 corridas (fragmentos, contexto, citas, tiempos)
│   ├── resultados_evaluacion.csv    # Tabla por pregunta y configuración
│   └── tabla_metricas_finales.csv   # Resumen de indicadores oficiales
├── .env.example                     # Plantilla de variables de entorno (sin claves)
├── requirements.txt                 # Dependencias Python
└── README.md
```

## Instalación y configuración

1. **Instalar dependencias:**

   ```bash
   pip install -r requirements.txt
   ```
2. **Configurar credenciales (sin exponer claves en el código):**
   Copia `.env.example` a `.env` en la raíz del proyecto y define tu clave de OpenRouter:

   ```env
   OPENROUTER_API_KEY=sk-or-...
   ```

   *(También puedes definir `API_KEY` o `OPENROUTER_API_KEY` como variable de entorno del sistema).*

## Ejecución paso a paso

1. Abrir y ejecutar todas las celdas de `notebooks/01_Base_R0.ipynb` para verificar la ingesta multi-formato, el diagnóstico de tokens y el funcionamiento de la configuración base **R0**.
2. Abrir y ejecutar todas las celdas de `notebooks/02_Experimentos_y_Evaluacion.ipynb` para correr las 45 evaluaciones (`R0`, `R1`, `R2`, `C0`, `R0_ALT` sobre las 9 preguntas) y regenerar los archivos en `resultados/`.

# Asistente SOC con RAG — NovaCloud Corp

Prototipo de sistema **RAG (Retrieval-Augmented Generation)** para consultas sobre normativa de seguridad, playbooks de respuesta a incidentes, matriz de SLA/escalamiento, hardening de servidores e historial de incidentes resueltos, con trazabilidad documental (`[Archivo | Localizador]`) y abstención ante evidencia insuficiente.

## Información Académica e Integrantes

* **Universidad:** Universidad Nacional de Colombia — Sede Manizales
* **Departamento:** Informática y Computación
* **Asignatura:** Sistemas Inteligentes Computacionales (2026-2) — Parcial 2 Práctico Sustentable
* **Integrantes:**
  * Jacobo Contreras Arango
  * Felipe Grisales López
  * Jhoan Sebastián Martínez Martínez

---

## Estructura del Proyecto

```text
RAG_Asistente_Ciberseguridad_SOC/
├── corpus/                                    # 5 documentos sintéticos en 3 formatos (.pdf, .docx, .md)
│   ├── Guia_Hardening_Red_y_Servidores.pdf
│   ├── Matriz_SLA_y_Escalamiento.docx
│   ├── Playbook_Respuesta_Incidentes.md
│   ├── Politica_Seguridad_y_Accesos.pdf
│   └── Registro_Incidentes_Resueltos.md
├── docs/                                      # Enunciado del proyecto e Informe técnico final
│   ├── Enunciado_Proyecto_RAG.docx
│   └── Informe_Proyecto_RAG.pdf
├── notebooks/
│   ├── rag_core.py                            # Módulo compartido (ingesta, chunking, denso/BM25, LLM)
│   ├── 01_Base_R0.ipynb                       # Prototipo base R0 y pruebas de desarrollo
│   └── 02_Experimentos_y_Evaluacion.ipynb     # Variantes R1, R2, C0, R0_ALT y 45 corridas
├── resultados/
│   ├── resultados_corridas.json               # Registro completo de las 45 corridas (fragmentos, contexto, citas, tiempos)
│   ├── resultados_evaluacion.csv              # Tabla detallada por pregunta y configuración
│   └── tabla_metricas_finales.csv             # Resumen oficial de indicadores
├── .env.example                               # Plantilla de variables de entorno (sin claves)
├── .gitignore                                 # Exclusión de credenciales (.env) y archivos de caché
├── requirements.txt                           # Dependencias del proyecto
└── README.md
```

---

## Configuraciones Evaluadas y Resumen de Resultados

Se evaluaron **9 preguntas** (3 directas, 3 combinadas entre $\ge 2$ documentos y 3 sin respuesta en el corpus) a través de **5 configuraciones** (**45 corridas** en total, 0 fallos):

| Configuración | Fragmentación | Recuperación | Embedder / LLM | Cob. Contexto | Corrección | Respaldo Citas | Abstención | Tiempo Prom. |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **R0 · Base** | Fija (`400` chars / `60` overlap) | Densa (coseno, `k=4`) | `paraphrase-multilingual-MiniLM-L12-v2` / `deepseek-chat` | `4/6` | `4/6` | `5/6 (83.3%)` | `3/3` | `4.12 s` |
| **R1 · Fragmentación** | Por sección/oración ($\le 500$ chars) | Densa (coseno, `k=4`) | Igual a R0 | `2/6` | `2/6` | `6/6 (100%)` | `3/3` | `3.78 s` |
| **R2 · Híbrida (Recomendada)** | Igual a R0 (`56` chunks) | `0.6 Denso + 0.4 BM25` (`k=4`) | Igual a R0 | **`4/6`** | **`4/6`** | **`6/6 (100%)`** | **`3/3`** | **`3.93 s`** |
| **C0 · Control sin RAG** | Sin documentos | Sin recuperación | N/A / `deepseek-chat` | `N/A` | `0/6` | `No aplica` | `2/3` | `4.91 s` |
| **R0_ALT · Modelo Alterno** | Igual a R0 (`56` chunks) | Densa (coseno, `k=4`) | `all-MiniLM-L6-v2` / `qwen-2.5-72b-instruct` | `2/6` | `1/6` | `5/6 (83.3%)` | `3/3` | `3.35 s` |

---

## Instalación y Configuración

1. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar credenciales (sin exponer claves en el código):**
   Define tu clave de OpenRouter como variable de entorno en tu sistema (`OPENROUTER_API_KEY` o `API_KEY`), o copia `.env.example` a `.env` en la raíz del proyecto:
   ```env
   OPENROUTER_API_KEY=sk-or-...
   ```

---

## Ejecución Paso a Paso

1. Abrir y ejecutar todas las celdas de [`notebooks/01_Base_R0.ipynb`](notebooks/01_Base_R0.ipynb) para verificar la ingesta multi-formato, el diagnóstico de límite de tokens (`0` fragmentos excedidos sobre `128` tokens) y el funcionamiento de la configuración base **R0**.
2. Abrir y ejecutar todas las celdas de [`notebooks/02_Experimentos_y_Evaluacion.ipynb`](notebooks/02_Experimentos_y_Evaluacion.ipynb) para ejecutar las 45 corridas (`R0`, `R1`, `R2`, `C0`, `R0_ALT`) y regenerar los reportes en `resultados/`.
3. Consultar el análisis detallado y la sustentación metodológica en [`docs/Informe_Proyecto_RAG.pdf`](docs/Informe_Proyecto_RAG.pdf).

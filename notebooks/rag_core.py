"""
Módulo compartido de utilidades RAG para el Asistente SOC (NovaCloud Corp).
Centraliza la ingesta multi-formato, fragmentación, recuperación densa/híbrida y consulta al LLM.
"""

import os
import re
import time
import numpy as np
from pypdf import PdfReader
from docx import Document
from rank_bm25 import BM25Okapi


PLANTILLA_SISTEMA_RAG = (
    "Eres un asistente técnico del Centro de Operaciones de Seguridad (SOC) de NovaCloud Corp. "
    "Responde únicamente con base en los fragmentos de contexto provistos. "
    "Cada afirmación debe incluir su cita exacta entre corchetes con el formato [Archivo | Localizador]. "
    "Si el contexto no contiene información suficiente para responder la pregunta de forma completa y verificable, "
    "debes abstenerte respondiendo exactamente: 'No encuentro evidencia suficiente en los documentos del corpus para responder esta pregunta.' "
    "No uses conocimiento externo ni inventes datos."
)

PLANTILLA_SISTEMA_C0 = (
    "Eres un asistente técnico de ciberseguridad. "
    "Responde a la pregunta usando únicamente tu conocimiento general. "
    "No tienes acceso a documentos internos de ninguna empresa; si la pregunta exige políticas, tiempos SLA, "
    "registros o configuraciones internas específicas que no conoces con certeza, indícalo explícitamente y abstente de inventar datos."
)


def resolver_ruta(nombre_carpeta):
    """Resuelve una carpeta relativa (ej. 'corpus' o 'resultados') desde raíz o desde notebooks/."""
    if os.path.isdir(nombre_carpeta):
        return nombre_carpeta
    padre = os.path.join("..", nombre_carpeta)
    if os.path.isdir(padre):
        return padre
    return padre


def cargar_env_local():
    """Carga variables de .env o ../.env si no están ya definidas en os.environ."""
    for ruta in [".env", os.path.join("..", ".env")]:
        if os.path.isfile(ruta):
            with open(ruta, encoding="utf-8") as f:
                for linea in f:
                    linea = linea.strip()
                    if not linea or linea.startswith("#") or "=" not in linea:
                        continue
                    k, v = linea.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k and k not in os.environ:
                        os.environ[k] = v


def cargar_corpus(carpeta="corpus"):
    """Lee archivos .pdf, .docx y .md conservando archivo y localizador verificable."""
    carpeta = resolver_ruta(carpeta)
    if not os.path.isdir(carpeta):
        raise FileNotFoundError(f"No existe la carpeta del corpus: {carpeta}")

    registros = []
    for nombre in sorted(os.listdir(carpeta)):
        ruta = os.path.join(carpeta, nombre)
        ext = os.path.splitext(nombre)[1].lower()

        if ext == ".pdf":
            reader = PdfReader(ruta)
            for num_pag, page in enumerate(reader.pages, start=1):
                texto = (page.extract_text() or "").strip()
                if texto:
                    texto_limpio = re.sub(r"\s+", " ", texto).strip()
                    registros.append({
                        "archivo": nombre,
                        "localizador": f"Página {num_pag}",
                        "seccion": f"Página {num_pag}",
                        "texto": texto_limpio,
                    })

        elif ext == ".docx":
            doc = Document(ruta)
            seccion_actual = "Inicio"
            for idx, p in enumerate(doc.paragraphs, start=1):
                txt = p.text.strip()
                if not txt:
                    continue
                if p.style and p.style.name.startswith("Heading"):
                    seccion_actual = txt
                registros.append({
                    "archivo": nombre,
                    "localizador": f"Sección '{seccion_actual}' (Párrafo {idx})",
                    "seccion": seccion_actual,
                    "texto": txt,
                })
            for t_idx, tabla in enumerate(doc.tables, start=1):
                filas_txt = []
                for row in tabla.rows:
                    celdas = [c.text.strip() for c in row.cells if c.text.strip()]
                    if celdas:
                        filas_txt.append(" | ".join(celdas))
                if filas_txt:
                    registros.append({
                        "archivo": nombre,
                        "localizador": f"Tabla {t_idx}",
                        "seccion": f"Tabla {t_idx}",
                        "texto": "\n".join(filas_txt),
                    })

        elif ext == ".md":
            with open(ruta, "r", encoding="utf-8") as f:
                lineas = f.readlines()
            seccion_actual = "Inicio"
            bloque, inicio_linea = [], 1
            for num_linea, linea in enumerate(lineas, start=1):
                limpia = linea.strip()
                if limpia.startswith("#"):
                    if bloque:
                        registros.append({
                            "archivo": nombre,
                            "localizador": f"Sección '{seccion_actual}' (Líneas {inicio_linea}-{num_linea - 1})",
                            "seccion": seccion_actual,
                            "texto": " ".join(bloque),
                        })
                        bloque = []
                    seccion_actual = limpia.lstrip("#").strip()
                    inicio_linea = num_linea
                    bloque.append(seccion_actual)
                elif limpia and set(limpia) != {"-"}:
                    if not bloque:
                        inicio_linea = num_linea
                    bloque.append(limpia)
            if bloque:
                registros.append({
                    "archivo": nombre,
                    "localizador": f"Sección '{seccion_actual}' (Líneas {inicio_linea}-{len(lineas)})",
                    "seccion": seccion_actual,
                    "texto": " ".join(bloque),
                })

    return registros


def fragmentar_tamano_fijo(unidades, chunk_size=400, overlap=60):
    """Fragmentación por tamaño fijo (caracteres) con solapamiento."""
    chunks = []
    paso = max(1, chunk_size - overlap)
    chunk_id = 0

    for u in unidades:
        texto = u["texto"]
        if len(texto) <= chunk_size:
            chunks.append({
                "id": chunk_id,
                "archivo": u["archivo"],
                "localizador": u["localizador"],
                "texto": texto,
            })
            chunk_id += 1
        else:
            inicio = 0
            parte = 1
            while inicio < len(texto):
                fin = min(len(texto), inicio + chunk_size)
                fragmento = texto[inicio:fin].strip()
                if fragmento:
                    chunks.append({
                        "id": chunk_id,
                        "archivo": u["archivo"],
                        "localizador": f"{u['localizador']} [Parte {parte}]",
                        "texto": fragmento,
                    })
                    chunk_id += 1
                    parte += 1
                if fin == len(texto):
                    break
                inicio += paso
    return chunks


def fragmentar_por_seccion(unidades, max_chars=500):
    """
    R1: Fragmentación por unidad estructural (sección/párrafo/oración) con límite similar,
    evitando cortar ideas a mitad de palabra y agrupando párrafos cortos de la misma sección.
    """
    chunks = []
    chunk_id = 0

    for u in unidades:
        texto = u["texto"]
        if len(texto) <= max_chars:
            chunks.append({
                "id": chunk_id,
                "archivo": u["archivo"],
                "localizador": u["localizador"],
                "texto": texto,
            })
            chunk_id += 1
        else:
            oraciones = [o.strip() for o in re.split(r"(?<=[.!?])\s+", texto) if o.strip()]
            actual, largo, parte = [], 0, 1
            for orac in oraciones:
                if actual and largo + len(orac) > max_chars:
                    chunks.append({
                        "id": chunk_id,
                        "archivo": u["archivo"],
                        "localizador": f"{u['localizador']} [Bloque {parte}]",
                        "texto": " ".join(actual),
                    })
                    chunk_id += 1
                    parte += 1
                    actual, largo = [], 0
                actual.append(orac)
                largo += len(orac)
            if actual:
                chunks.append({
                    "id": chunk_id,
                    "archivo": u["archivo"],
                    "localizador": f"{u['localizador']} [Bloque {parte}]",
                    "texto": " ".join(actual),
                })
                chunk_id += 1
    return chunks


def tokenizar_bm25(texto):
    return re.findall(r"\w+", texto.lower())


def construir_indice_bm25(chunks):
    corpus_tok = [tokenizar_bm25(c["texto"]) for c in chunks]
    return BM25Okapi(corpus_tok)


def recuperar_denso(pregunta, chunks, chunk_embeddings, embedder, top_k=4):
    query_emb = embedder.encode(pregunta, normalize_embeddings=True)
    similitudes = chunk_embeddings @ query_emb
    top_indices = np.argsort(similitudes)[::-1][:top_k]
    return [
        {
            "rank": rank + 1,
            "score": float(similitudes[i]),
            "archivo": chunks[i]["archivo"],
            "localizador": chunks[i]["localizador"],
            "texto": chunks[i]["texto"],
        }
        for rank, i in enumerate(top_indices)
    ]


def recuperar_hibrido(pregunta, chunks, chunk_embeddings, embedder, bm25, top_k=4, peso_denso=0.6):
    """
    R2: Recuperación híbrida combinando similitud coseno (densa) y BM25 (léxica)
    mediante normalización min-max, conservando el mismo top_k.
    """
    query_emb = embedder.encode(pregunta, normalize_embeddings=True)
    scores_denso = chunk_embeddings @ query_emb
    scores_bm25 = np.array(bm25.get_scores(tokenizar_bm25(pregunta)), dtype=float)

    def _minmax(arr):
        rango = arr.max() - arr.min()
        return (arr - arr.min()) / rango if rango > 1e-9 else np.zeros_like(arr)

    comb = peso_denso * _minmax(scores_denso) + (1.0 - peso_denso) * _minmax(scores_bm25)
    top_indices = np.argsort(comb)[::-1][:top_k]
    return [
        {
            "rank": rank + 1,
            "score": float(comb[i]),
            "score_denso": float(scores_denso[i]),
            "score_bm25": float(scores_bm25[i]),
            "archivo": chunks[i]["archivo"],
            "localizador": chunks[i]["localizador"],
            "texto": chunks[i]["texto"],
        }
        for rank, i in enumerate(top_indices)
    ]


def construir_contexto(recuperados, max_chars=6000):
    bloques = []
    acumulado = 0
    recortado = False
    for r in recuperados:
        bloque = f"[{r['archivo']} | {r['localizador']}] (score={r['score']:.3f})\n{r['texto']}"
        if acumulado + len(bloque) > max_chars:
            recortado = True
            break
        bloques.append(bloque)
        acumulado += len(bloque) + 2
    return "\n\n".join(bloques), recortado


def consultar_rag_con_recuperados(client, pregunta, recuperados, modelo_llm,
                                  temperatura=0.0, max_tokens=500, max_contexto_chars=6000):
    if client is None:
        raise RuntimeError("Cliente OpenRouter no inicializado. Define API_KEY_THREE u OPENROUTER_API_KEY.")
    t0 = time.perf_counter()
    contexto, recortado = construir_contexto(recuperados, max_chars=max_contexto_chars)

    prompt_usuario = f"""Contexto recuperado:
{contexto}

Pregunta: {pregunta}

Instrucción: Responde en español, de forma precisa, citando [Archivo | Localizador] en cada afirmación."""

    response = client.chat.completions.create(
        model=modelo_llm,
        messages=[
            {"role": "system", "content": PLANTILLA_SISTEMA_RAG},
            {"role": "user", "content": prompt_usuario},
        ],
        temperature=temperatura,
        max_tokens=max_tokens,
    )
    latencia = time.perf_counter() - t0
    return {
        "pregunta": pregunta,
        "respuesta": response.choices[0].message.content,
        "recuperados": recuperados,
        "contexto_enviado": contexto,
        "contexto_recortado": recortado,
        "tiempo_seg": round(latencia, 2),
    }


def consultar_control_c0(client, pregunta, modelo_llm, temperatura=0.0, max_tokens=500):
    """C0: Control sin recuperación (Sin RAG ni citas documentales)."""
    if client is None:
        raise RuntimeError("Cliente OpenRouter no inicializado. Define API_KEY_THREE u OPENROUTER_API_KEY.")
    t0 = time.perf_counter()
    response = client.chat.completions.create(
        model=modelo_llm,
        messages=[
            {"role": "system", "content": PLANTILLA_SISTEMA_C0},
            {"role": "user", "content": f"Pregunta: {pregunta}\nResponde en español de forma breve y precisa."},
        ],
        temperature=temperatura,
        max_tokens=max_tokens,
    )
    latencia = time.perf_counter() - t0
    return {
        "pregunta": pregunta,
        "respuesta": response.choices[0].message.content,
        "recuperados": [],
        "contexto_enviado": "",
        "contexto_recortado": False,
        "tiempo_seg": round(latencia, 2),
    }

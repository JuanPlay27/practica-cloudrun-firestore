from fastapi import FastAPI, HTTPException, Request
from google.cloud import firestore
import os

# Carga de variables de entorno
# PROJECT_ID: ID del proyecto de GCP donde existe Firestore
project_id = os.environ["GOOGLE_CLOUD_PROJECT"]
# DATABASE_ID: Nombre de la base de datos Firestore (db-notes)
database_id = os.environ["FIRESTORE_DATABASE"]

# Inicialización del cliente de Firestore
# Creamos el cliente de Firestore pasándole explícitamente el project_id y el database_id
db = firestore.Client(project=project_id, database=database_id)

# Configuración de la app FastAPI
app = FastAPI(title="Notas con Firestore real")

# Endpoint: Listar todas las notas
# Método: GET /notes
@app.get("/notes")
async def list_notes():
    # 1. Accedemos a la colección "notes"
    docs = db.collection("notes").stream()
    # 2. Convertimos cada documento en un diccionario con su ID y datos
    return [{"id": d.id, **d.to_dict()} for d in docs]

# Endpoint: Crear una nueva nota
# Método: POST /notes
@app.post("/notes")
async def create_note(req: Request):
    # 1. Leemos el JSON del cuerpo de la petición
    data = await req.json()

    # 2. Validamos que existan los campos obligatorios 'title' y 'content'
    if not data.get("title") or not data.get("content"):
        raise HTTPException(status_code=400, detail="Faltan 'title' o 'content'")

    # 3. Creamos un nuevo documento con ID automático en la colección "notes"
    ref = db.collection("notes").document()

    # 4. Guardamos los datos junto con la fecha de creación del servidor
    ref.set({
        "title": data["title"],
        "content": data["content"],
        # SERVER_TIMESTAMP inserta la fecha/hora actual del servidor
        "created_at": firestore.SERVER_TIMESTAMP
    })

    # 5. Devolvemos el ID del documento recién creado
    return {"id": ref.id}

# Endpoint: Actualizar una nota existente
# Método: PUT /notes/{id}
@app.put("/notes/{id}")
async def update_note(id: str, req: Request):
    # 1. Leemos el JSON del cuerpo de la petición
    data = await req.json()

    # 2. Validamos que existan los campos 'title' y 'content'
    if not data.get("title") or not data.get("content"):
        raise HTTPException(status_code=400, detail="Faltan 'title' o 'content'")

    # 3. Obtenemos la referencia al documento con el ID proporcionado
    ref = db.collection("notes").document(id)

    # 4. Verificamos si el documento existe
    if not ref.get().exists:
        raise HTTPException(status_code=404, detail="Nota no encontrada")

    # 5. Actualizamos el documento con los nuevos datos
    ref.update({
        "title": data["title"],
        "content": data["content"],
        # Agregamos una marca de tiempo de última actualización
        "updated_at": firestore.SERVER_TIMESTAMP
    })

    # 6. Devolvemos confirmación de actualización
    return {"message": "Nota actualizada exitosamente", "id": id}

# Endpoint: Eliminar una nota
# Método: DELETE /notes/{id}
@app.delete("/notes/{id}")
async def delete_note(id: str):
    # 1. Obtenemos la referencia al documento con el ID proporcionado
    ref = db.collection("notes").document(id)

    # 2. Verificamos si el documento existe
    if not ref.get().exists:
        raise HTTPException(status_code=404, detail="Nota no encontrada")

    # 3. Eliminamos el documento
    ref.delete()

    # 4. Devolvemos confirmación de eliminación
    return {"message": "Nota eliminada exitosamente", "id": id}
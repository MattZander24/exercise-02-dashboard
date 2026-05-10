from fastapi import FastAPI, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from contextlib import asynccontextmanager

from .database import engine, Base, get_db
from . import models, schemas

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        active_nodes_count = db.query(models.Node).filter(models.Node.status == "active").count()
        return {"status": "ok", "db": "connected", "nodes_count": active_nodes_count}
    except Exception:
        return {"status": "ok", "db": "error", "nodes_count": 0}

@app.post("/api/nodes", response_model=schemas.NodeResponse, status_code=status.HTTP_201_CREATED)
def create_node(node: schemas.NodeCreate, db: Session = Depends(get_db)):
    db_node = db.query(models.Node).filter(models.Node.name == node.name).first()
    if db_node:
        raise HTTPException(status_code=409, detail="Node already exists")
    new_node = models.Node(name=node.name, host=node.host, port=node.port, status="active")
    db.add(new_node)
    db.commit()
    db.refresh(new_node)
    return new_node

@app.get("/api/nodes", response_model=list[schemas.NodeResponse])
def list_nodes(db: Session = Depends(get_db)):
    return db.query(models.Node).all()

@app.get("/api/nodes/{name}", response_model=schemas.NodeResponse)
def get_node(name: str, db: Session = Depends(get_db)):
    db_node = db.query(models.Node).filter(models.Node.name == name).first()
    if not db_node:
        raise HTTPException(status_code=404, detail="Node not found")
    return db_node

@app.put("/api/nodes/{name}", response_model=schemas.NodeResponse)
def update_node(name: str, node_update: schemas.NodeUpdate, db: Session = Depends(get_db)):
    db_node = db.query(models.Node).filter(models.Node.name == name).first()
    if not db_node:
        raise HTTPException(status_code=404, detail="Node not found")
    update_data = node_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_node, key, value)
    db_node.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_node)
    return db_node

@app.delete("/api/nodes/{name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_node(name: str, db: Session = Depends(get_db)):
    db_node = db.query(models.Node).filter(models.Node.name == name).first()
    if not db_node:
        raise HTTPException(status_code=404, detail="Node not found")
    db_node.status = "inactive"
    db_node.updated_at = datetime.utcnow()
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.repository.empresa import EmpresaRepository
# --- 1. Importa el repo y el modelo de asignación ---
from app.repository.empresa_representante import EmpresaRepresentanteRepository
from app.models.empresa_representante import EmpresaRepresentanteCreate
from app.models.empresa import EmpresaCreate, EmpresaUpdate
from typing import Optional
from sqlalchemy.exc import IntegrityError

class EmpresaService:
    def __init__(self):
        self.repository = EmpresaRepository()
        # --- 2. Instancia el repo de asignación (o inyéctalo si usas dependencias) ---
        self.empresa_rep_repo = EmpresaRepresentanteRepository()

    def get_all_empresas(self, db: Session, proyecto_id: Optional[int] = None):
        """ Obtiene todas las empresas, filtrando opcionalmente por proyecto. """
        return self.repository.get_all(db, proyecto_id=proyecto_id)

    def get_empresa_by_id(self, db: Session, id: int):
        """ Obtiene una empresa por ID, con validación. """
        empresa = self.repository.get_by_id(db, id)
        if not empresa:
            raise HTTPException(status_code=404, detail="Empresa no encontrada")
        return empresa

    # --- 3. MODIFICAR create_empresa ---
    def create_empresa(self, db: Session, empresa_data: EmpresaCreate):
        """
        Crea una nueva empresa, valida duplicados y asigna proyecto/representantes.
        """
        # Validar duplicados por razón social
        empresa_existente = self.repository.get_by_razon_social(db, empresa_data.razon_social)
        if empresa_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe una empresa con la Razón Social '{empresa_data.razon_social}'."
            )

        # Crear el objeto EmpresaCreate *solo* con los campos de la tabla empresa
        # para pasarlo al repositorio. Excluimos proyecto_id y representante_ids.
        empresa_payload_dict = empresa_data.model_dump(exclude={'proyecto_id', 'representante_ids'})
        empresa_payload_for_repo = EmpresaCreate(**empresa_payload_dict)

        # Crear la empresa principal
        nueva_empresa = self.repository.create(db, empresa_payload_for_repo)
        
        # Asignar Proyecto si se proporcionó un ID válido
        if empresa_data.proyecto_id is not None: # Verifica que no sea None
             try:
                 # Llama al método del repo de empresa que asigna proyecto
                 self.repository.asignar_proyecto(db, empresa_id=nueva_empresa.id, proyecto_id=empresa_data.proyecto_id)
             except Exception as e:
                 # Si falla la asignación, podrías querer deshacer la creación (aunque el rollback lo hará el endpoint)
                 print(f"Error asignando proyecto {empresa_data.proyecto_id} a empresa {nueva_empresa.id}: {e}")
                 # Podrías relanzar una excepción específica si quieres manejarla diferente en el endpoint
                 # raise HTTPException(status_code=500, detail=f"Error asignando proyecto: {e}")

        # Asignar Representantes si se proporcionó una lista válida de IDs
        if empresa_data.representante_ids: # Verifica que la lista no esté vacía
            for rep_id in empresa_data.representante_ids:
                 try:
                     # Llama al método del repo de empresa_representante
                     asignacion = EmpresaRepresentanteCreate(empresa_id=nueva_empresa.id, representante_id=rep_id)
                     self.empresa_rep_repo.asignar(db, asignacion) # Este repo NO debe hacer commit
                 except Exception as e:
                     # Manejo de error similar al de proyecto
                     print(f"Error asignando representante {rep_id} a empresa {nueva_empresa.id}: {e}")
                     # raise HTTPException(status_code=500, detail=f"Error asignando representante: {e}")

        # Devuelve la empresa recién creada (sin los IDs de proyecto/reps necesariamente,
        # a menos que get_by_id los devuelva, lo cual no es lo usual para el create)
        # El endpoint hará commit después de esto
        return nueva_empresa

    def update_empresa(self, db: Session, id: int, empresa: EmpresaUpdate):
        """ Actualiza una empresa. """
        # NOTA: Para actualizar proyecto/representantes aquí, necesitarías lógica similar
        # a la de create_empresa: obtener asignaciones actuales, comparar con las nuevas,
        # y llamar a los métodos de asignar/desasignar correspondientes.
        self.repository.update(db, id, empresa)
        # El endpoint hará commit
        return {"message": "Empresa actualizada exitosamente"}

    def delete_empresa(self, db: Session, id: int):
        """ Elimina (lógicamente) una empresa. """
        # NOTA: Considera si al eliminar una empresa deberías desasignar
        # automáticamente sus representantes/proyectos (depende de tu FK y lógica).
        # El endpoint hará commit
        return self.repository.delete(db, id)

    def asignar_proyecto(self, db: Session, empresa_id: int, proyecto_id: int):
        """ Asigna un proyecto a una empresa. """
        # El endpoint hará commit
        return self.repository.asignar_proyecto(db, empresa_id, proyecto_id)
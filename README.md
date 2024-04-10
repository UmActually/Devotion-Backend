# D. E. V. O. T. I. O. N.

> Development Environment for the Visualization of Organizational Tasks Inspired Obviously by Notion

## Setup del back end

Requiere Python 3.9 o superior. TODO: Falta ver temitas de Gunicorn y hosting en producción.

```bash
pip install -r requirements.txt
python manage.py runserver
```

## API bonita

☆ = Requiere autenticación de token Bearer.

Para crear o actualizar un recurso, el usuario debe ser líder del proyecto papá. La única excepción a esto es PUT `/tasks/<id>/status/`, que puede ser ejecutado por cualquier miembro del proyecto. Ser un superuser sobrepasa todas estas restricciones. 

- GET `/test/` - _Hola, mundo_

**Users**

- POST `/users/` - _Crear usuario_
- POST `/login/` - _Iniciar sesión_
- GET `/me/` - _Obtener usuario ☆_
- PUT `/me/` - _Actualizar usuario ☆_
- GET `/me/projects/` - _Obtener proyectos del usuario ☆_

**Projects**

- POST `/projects/` - _Crear proyecto ☆_
- GET `/projects/<id>/` - _Obtener proyecto_
- GET `/projects/<id>/subtasks/` - _Obtener todas las subtareas del proyecto_
- PUT `/projects/<id>/` - _Actualizar proyecto ☆_
- DELETE `/projects/<id>/` - _Eliminar proyecto ☆_

**Tasks**

- POST `/tasks/` - _Crear tarea ☆_
- GET `/tasks/<id>/` - _Obtener tarea_
- GET `/tasks/<id>/subtasks/` - _Obtener todas las subtareas de la tarea_
- PUT `/tasks/<id>/` - _Actualizar tarea ☆_
- PUT `/tasks/<id>/status/` - _Cambiar estado de tarea ☆_
- DELETE `/tasks/<id>/` - _Eliminar tarea ☆_

**Dashboard (Aún no tan)**

- GET `/projects/<id>/dashboard/` - _Obtener dashboard del proyecto_
- POST `/projects/<id>/dashboard/widgets/` - _Crear widget_
- PUT `/projects/<id>/dashboard/widgets/` - _Actualizar widget_
- POST `/projects/<id>/dashboard/sources/` - _Crear fuente de datos_

### Users

#### POST `/users/` - _Crear usuario_

**Entrada**

- `email`
- `password`
- `first_names`
- `last_names`

**Salida**

```json
{
  "id": 1,
  "token": "eyJ0..."
}
```

### Projects

#### POST `/projects/` - _Crear proyecto ☆_

**Entrada**

- `name`
- `description`
- `parent` (opcional) - _ID del proyecto papá_
- `leaders` - _IDs de usuarios líderes separados por ","_
- `members` - _IDs de usuarios miembros separados por ","_

### Tasks

#### POST `/tasks/` - _Crear tarea ☆_

**Entrada**

- `name`
- `description` (opcional)
- `priority` (opcional) - _Entero. 0 es baja, 1 es media, 2 es alta, default es 0_
- `start_date` (opcional) - _Fecha de inicio en formato YYYY-MM-DD, default es hoy, o `due_date` si ésta es del pasado_
- `due_date` - _Formato YYYY-MM-DD_
- `parent_project` - _ID del proyecto papá_
- `parent_task` (opcional) - _ID de la tarea papá_
- `asignee` - _ID del usuario asignado_

Powered by SALAD, Society of Academic Labor and Application Development.

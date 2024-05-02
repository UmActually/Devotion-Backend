# D. E. V. O. T. I. O. N.

> Development Environment for the Visualization of Organizational Tasks Inspired Obviously by Notion

## Setup del back end

Requiere Python 3.9 o superior.

```bash
pip install -r requirements.txt
gunicorn devotion.wsgi
```

## API bonita

☆ = Requiere autenticación de token Bearer.

Para crear o actualizar un recurso, el usuario debe ser líder del proyecto papá. La única excepción a esto es PUT `/tasks/<id>/status/`, que puede ser ejecutado por cualquier miembro del proyecto. Ser un superuser sobrepasa todas estas restricciones.

- GET `/test/` - _Hola, mundo_

**Users**

- POST `/users/` - _[Crear usuario](#post-users---crear-usuario)_
- POST `/login/` - _[Iniciar sesión](#post-login---iniciar-sesi%C3%B3n)_
- GET `/users/` - _[Obtener todos los usuarios ☆](#get-users---obtener-todos-los-usuarios-)_
- GET `/me/` - _[Obtener usuario ☆](#get-me---obtener-usuario-)_
- PUT `/me/` - _[Actualizar usuario ☆](#put-me---actualizar-usuario-)_
- GET `/me/projects/` - _[Obtener proyectos del usuario ☆](#get-meprojects---obtener-proyectos-del-usuario-)_

**Projects**

- POST `/projects/` - _[Crear proyecto ☆](#post-projects---crear-proyecto-)_
- GET `/projects/<id>/` - _[Obtener proyecto](#get-projectsid---obtener-proyecto)_
- GET `/projects/<id>/members/` - _[Obtener miembros del proyecto ☆](#get-projectsidmembers---obtener-miembros-del-proyecto-)_
- GET `/projects/<id>/subtasks/` - _[Obtener todas las subtareas del proyecto](#get-projectsidsubtasks---obtener-todas-las-subtareas-del-proyecto)_
- PUT `/projects/<id>/` - _[Actualizar proyecto ☆](#put-projectsid---actualizar-proyecto-)_
- DELETE `/projects/<id>/` - _[Eliminar proyecto ☆](#delete-projectsid---eliminar-proyecto-)_

**Tasks**

- POST `/tasks/` - _[Crear tarea ☆](#post-tasks---crear-tarea-)_
- GET `/tasks/<id>/` - _[Obtener tarea](#get-tasksid---obtener-tarea)_
- GET `/tasks/<id>/subtasks/` - _[Obtener todas las subtareas de la tarea](#get-tasksidsubtasks---obtener-todas-las-subtareas-de-la-tarea)_
- PUT `/tasks/<id>/` - _[Actualizar tarea ☆](#put-tasksid---actualizar-tarea-)_
- PUT `/tasks/<id>/status/` - _[Cambiar estado de tarea ☆](#put-tasksidstatus---cambiar-estado-de-tarea-)_
- DELETE `/tasks/<id>/` - _[Eliminar tarea ☆](#delete-tasksid---eliminar-tarea-)_

**Dashboard (Aún no tan)**

- GET `/projects/<id>/dashboard/` - _Obtener dashboard del proyecto_
- POST `/projects/<id>/dashboard/widgets/` - _Crear widget_
- PUT `/projects/<id>/dashboard/widgets/` - _Actualizar widget_
- POST `/projects/<id>/dashboard/sources/` - _Crear fuente de datos_

---

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

---

#### POST `/login/` - _Iniciar sesión_

**Entrada**

- `email`
- `password`

**Salida**

```json
{
  "access": "eyJ0...",
  "refresh": "eyJ0..."
}
```

---

#### GET `/users/` - _Obtener todos los usuarios ☆_

**Salida**

```json
[
  {
    "id": "e729a80d-0033-4e0e-8891-20085212b445",
    "email": "sergioperez@example.com",
    "firstNames": "Sergio",
    "lastNames": "Pérez"
  },
  {
    "id": "42e74cee-497c-41f5-834e-ac3578229cb6",
    "email": "lewishamilton@example.com",
    "firstNames": "Lewis",
    "lastNames": "Hamilton"
  },
  ...
]
```

---

#### GET `/me/` - _Obtener usuario ☆_

**Salida**

```json
{
  "id": "e729a80d-0033-4e0e-8891-20085212b445",
  "email": "sergioperez@example.com",
  "firstNames": "Sergio",
  "lastNames": "Pérez"
}
```

---

#### PUT `/me/` - _Actualizar usuario ☆_

**Entrada**

- `email` (opcional)
- `first_names` (opcional)
- `last_names` (opcional)

---

#### GET `/me/projects/` - _Obtener proyectos del usuario ☆_

**Salida**

```json
[
  {
    "id": "4bfca576-83d2-447a-9b79-cdc778417c84",
    "name": "FSAE 2024",
    "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Proin volutpat tortor eget lacus ultricies, nec ullamcorper risus viverra. Pellentesque non ultrices nibh."
  },
  ...
]
```

---

### Projects

#### POST `/projects/` - _Crear proyecto ☆_

**Entrada**

- `name`
- `description`
- `parent` (opcional) - _ID del proyecto papá_
- `leaders` - _IDs de usuarios líderes separados por ","_
- `members` - _IDs de usuarios miembros separados por ","_

---

#### GET `/projects/<id>/` - _Obtener proyecto_

**Salida**

```json
{
  "id": "887ebfdd-bd39-417c-9b42-90396c2b8e59",
  "name": "Chasis",
  "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Proin volutpat tortor eget lacus ultricies, nec ullamcorper risus viverra. Pellentesque non ultrices nibh.",
  "breadcrumbs": [
    [
      "4bfca576-83d2-447a-9b79-cdc778417c84",
      "FSAE 2024",
      false
    ],
    ...
  ],
  "projects": [
    {
      "id": "169bdff0-30d5-4b7f-ad7a-c2793a1a7328",
      "name": "Cockpit",
      "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Proin volutpat tortor eget lacus ultricies, nec ullamcorper risus viverra. Pellentesque non ultrices nibh."
    },
    ...
  ],
  "tasks": [
    {
      "id": "0191827d-1e38-4647-885c-aef73ea494b0",
      "name": "Peso y distribución",
      "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incidid.",
      "status": 3,
      "priority": 0,
      "startDate": "2024-02-13",
      "dueDate": "2024-02-21",
      "assignee": "Alexander Albon",
      "parentProject": "887ebfdd-bd39-417c-9b42-90396c2b8e59",
      "parentTask": null
    },
    ...
  ],
  "progress": 50
}
```

---

#### GET `/projects/<id>/members/` - _Obtener miembros del proyecto ☆_

**Salida**

```json
[
  {
    "id": "4fceb6df-d3ac-4f5a-b177-995ac5673d1a",
    "email": "valtteribottas@example.com",
    "firstNames": "Valtteri",
    "lastNames": "Bottas"
  },
  ...
]
```

---

#### GET `/projects/<id>/subtasks/` - _Obtener todas las subtareas del proyecto_

**Salida**

```json
[
  {
    "id": "0191827d-1e38-4647-885c-aef73ea494b0",
    "name": "Peso y distribución",
    "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incidid.",
    "status": 3,
    "priority": 0,
    "startDate": "2024-02-13",
    "dueDate": "2024-02-21",
    "assignee": "Alexander Albon",
    "parentProject": "887ebfdd-bd39-417c-9b42-90396c2b8e59",
    "parentTask": null
  },
  ...
]
```

TODO: Falta implementar.

---

#### PUT `/projects/<id>/` - _Actualizar proyecto ☆_

**Entrada**

- `name` (opcional)
- `description` (opcional)
- `parent` (opcional) - _ID del proyecto papá_
- `leaders` (opcional) - _IDs de usuarios líderes separados por ","_
- `members` (opcional) - _IDs de usuarios miembros separados por ","_

---

#### DELETE `/projects/<id>/` - _Eliminar proyecto ☆_

---

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
- `assignee` - _ID del usuario asignado_

---

#### GET `/tasks/<id>/` - _Obtener tarea_

**Salida**

```json
{
  "id": "0191827d-1e38-4647-885c-aef73ea494b0",
  "name": "Peso y distribución",
  "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incidid.",
  "status": 3,
  "priority": 0,
  "startDate": "2024-02-13",
  "dueDate": "2024-02-21",
  "assignee": "Alexander Albon",
  "breadcrumbs": [
    [
      "4bfca576-83d2-447a-9b79-cdc778417c84",
      "FSAE 2024",
      false
    ],
    ...
  ],
  "tasks": [
    {
      "id": "0191827d-1e38-4647-885c-aef73ea494b0",
      "name": "Peso y distribución",
      "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incidid.",
      "status": 3,
      "priority": 0,
      "startDate": "2024-02-13",
      "dueDate": "2024-02-21",
      "assignee": "Alexander Albon",
      "parentProject": "887ebfdd-bd39-417c-9b42-90396c2b8e59",
      "parentTask": null
    },
    ...
  ]
}
```

---

#### GET `/tasks/<id>/subtasks/` - _Obtener todas las subtareas de la tarea_

**Salida**

```json
[
  {
    "id": "0191827d-1e38-4647-885c-aef73ea494b0",
    "name": "Peso y distribución",
    "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incidid.",
    "status": 3,
    "priority": 0,
    "startDate": "2024-02-13",
    "dueDate": "2024-02-21",
    "assignee": "Alexander Albon",
    "parentProject": "887ebfdd-bd39-417c-9b42-90396c2b8e59",
    "parentTask": null
  },
  ...
]
```

TODO: Falta implementar.

---

#### PUT `/tasks/<id>/` - _Actualizar tarea ☆_

**Entrada**

- `name` (opcional)
- `description` (opcional)
- `priority` (opcional) - _Entero. 0 es baja, 1 es media, 2 es alta, default es 0_
- `start_date` (opcional) - _Fecha de inicio en formato YYYY-MM-DD, default es hoy, o `due_date` si ésta es del pasado_
- `due_date` (opcional) - _Formato YYYY-MM-DD_
- `parent_project` (opcional) - _ID del proyecto papá_
- `parent_task` (opcional) - _ID de la tarea papá_
- `assignee` (opcional) - _ID del usuario asignado_

---

#### PUT `/tasks/<id>/status/` - _Cambiar estado de tarea ☆_

**Entrada**

- `status` - _Entero. 0 es pendiente, 1 es en progreso, 2 es en revisión, 3 es completada_

---

#### DELETE `/tasks/<id>/` - _Eliminar tarea ☆_

---

Powered by SALAD, Society of Academic Labor and Application Development.

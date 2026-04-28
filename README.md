# Backend - Sistema de Talleres

API REST desarrollada con FastAPI para la gestión de usuarios, autenticación y registro a talleres/cursos.

---

## Tecnologías

- Python
- FastAPI
- PostgreSQL
- JWT (Autenticación)

---

## Estructura del proyecto

```
backend/
│── app/
│   ├── main.py
│   ├── routes/
│   ├── models/
│   ├── schemas/
│   ├── services/
│
│── database/
│   ├── schema.sql
│   ├── seed.sql
│
│── .env.example
│── requirements.txt
│── README.md
```

---

## Configuración

### 1. Clonar el repositorio

```
git clone <URL_DE_TU_REPOSITORIO>
cd backend
```

---

### 2. Crear archivo `.env`

Copia el archivo de ejemplo:

```
cp .env.example .env
```

---

### 3. Configurar variables de entorno

Edita el archivo `.env`:

```
PORT=8000

DB_HOST=localhost
DB_PORT=5432
DB_NAME=talleres_db
DB_USER=postgres
DB_PASSWORD=tu_password

JWT_SECRET=tu_secreto_seguro
JWT_EXPIRES_IN=7d
```

---

## Ejecución del proyecto

### 1. Instalar dependencias

```
pip install -r requirements.txt
```

---

### 2. Ejecutar servidor

```
uvicorn app.main:app --reload
```

---

### 3. Acceso

Servidor:

```
http://localhost:8000
```

Documentación interactiva:

```
http://localhost:8000/docs
```

---

## Base de datos

### 1. Crear base de datos en PostgreSQL

```
CREATE DATABASE talleres_db;
```

---

### 2. Ejecutar estructura

```
psql -U postgres -d talleres_db -f database/schema.sql
```

---

### 3. (Opcional) Insertar datos de prueba

```
psql -U postgres -d talleres_db -f database/seed.sql
```

---

## Autenticación

El sistema utiliza autenticación basada en JWT.

Flujo básico:

1. Registro de usuario
2. Inicio de sesión
3. Generación de token
4. Acceso a rutas protegidas

---

## Endpoints principales

- `POST /register` → Registrar usuario
- `POST /login` → Iniciar sesión
- `GET /users` → Obtener usuarios
- `POST /cursos` → Crear curso

📖 Consulta todos los endpoints en:

```
/docs
```

---

## Notas importantes

- El archivo `.env` **no debe subirse** al repositorio
- Usar `.env.example` como referencia
- Asegúrate de configurar correctamente la base de datos antes de ejecutar

---

## Mejoras futuras

- Sistema de roles (admin / usuario)
- Validaciones avanzadas
- Deploy en la nube
- Logs y manejo de errores más robusto

---

## Autor

Proyecto desarrollado como parte de aprendizaje en backend y desarrollo web.

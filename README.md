# Sistema de Ventas Online (Microservicios)

Este proyecto implementa una solución de entrega de contenido (e-commerce) basada en arquitectura de microservicios, desplegada con contenedores Docker, y un pipeline de CI/CD hacia AWS.

## Arquitectura

El sistema está compuesto por 3 microservicios/contenedores principales:
1. **Frontend (Angular)**: Interfaz de usuario para visualizar productos, gestionar carrito y pagar.
2. **Backend API (FastAPI)**: Gestión de usuarios, productos, carrito y órdenes.
3. **Microservicio de Pagos (FastAPI)**: Integración con Mercado Pago para procesar transacciones.
4. **Base de Datos (PostgreSQL)**: Persistencia de datos.

## Requisitos Previos

- Docker y Docker Compose instalados.
- Node.js (opcional, para desarrollo frontend local).
- Python 3.11+ (opcional, para desarrollo backend local).
- Cuenta de AWS (para el pipeline CI/CD).
- Cuenta de Mercado Pago (para obtener Access Token).

## Ejecución Local

1. Clonar el repositorio.
2. Levantar los servicios con Docker Compose:
   ```bash
   docker-compose up --build -d
   ```
3. Accesos:
   - Frontend: `http://localhost:4200`
   - Backend API Docs: `http://localhost:8000/docs`
   - Pagos API Docs: `http://localhost:8002/docs`

## Pipeline CI/CD

El repositorio incluye un workflow de GitHub Actions (`.github/workflows/deploy.yml`) que:
- Construye las imágenes Docker automáticamente.
- Sube las imágenes a AWS ECR.
- Despliega las nuevas imágenes en AWS ECS (Fargate).

### Configuración en AWS y GitHub:
1. Crear 3 repositorios en Amazon ECR (`frontend-repo`, `backend-repo`, `pagos-repo`).
2. Crear un Cluster ECS (`ecommerce-cluster`).
3. Crear Task Definitions y Services en ECS para cada contenedor.
4. Configurar los Secrets en el repositorio de GitHub:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`

## Demostración (Presentación)

Para la demostración en vivo de CI/CD:
1. Realice un cambio visible en el código (por ejemplo, en `frontend/src/app/app.component.html`).
2. Haga `git commit` y `git push` a la rama `main`.
3. Muestre cómo se ejecuta GitHub Actions y cómo se actualiza en AWS automáticamente.

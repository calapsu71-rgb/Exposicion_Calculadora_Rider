# Definition of Done (DoD) - Proyecto LastBite

Para que una Historia de Usuario o funcionalidad de **LastBite** se considere terminada (Done) y lista para presentar en la validación, debe cumplir con los siguientes criterios:

1. **Código y Control de Versiones:**
   - [ ] El código ha sido subido al repositorio en GitHub (rama `main` o `develop`).
   - [ ] No hay errores de sintaxis ni "warnings" críticos en la consola.
   - [ ] El código está debidamente comentado (especialmente la lógica de reservas y estados).

2. **Backend y Base de Datos (Python/Flask & MongoDB):**
   - [ ] Los endpoints creados responden con los códigos de estado HTTP correctos (200, 201, 400, 404, 500).
   - [ ] Las consultas a la base de datos están optimizadas.
   - [ ] Los datos sensibles (contraseñas) están encriptados.

3. **Pruebas y QA:**
   - [ ] Se han probado los flujos principales en al menos un navegador de escritorio y un dispositivo móvil.
   - [ ] Se verificaron las validaciones de los formularios (campos vacíos, formatos incorrectos).

4. **Documentación:**
   - [ ] El diagrama Entidad-Relación (o esquema de colecciones) ha sido actualizado si hubo cambios.
   - [ ] El archivo `README.md` incluye instrucciones sobre cómo ejecutar la nueva funcionalidad.
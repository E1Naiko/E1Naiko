# Guía para trabajar en este repositorio

Este es un repositorio de perfil de GitHub. Conservá el contenido de perfil del `README.md` raíz. La implementación del bot vive en `correlativas/`; su [guía de uso](correlativas/README.md) es la referencia para comandos y ejemplos.

## Dónde hacer cambios

- **Comandos y permisos:** `correlativas/bot.py`. `Bot.responder(usuario, mensaje)` recibe el ID del remitente y devuelve texto; mantené la lógica independiente de la consola o plataforma de chat. Un adaptador debe pasar el ID autenticado, nunca uno indicado en el mensaje. Los comandos `admin` requieren autorización explícita mediante `BOT_ADMIN_IDS` o el parámetro `admins`.
- **Catálogo inicial:** `correlativas/planes/<plan>.json`. El nombre del archivo identifica al plan; cada código de materia tiene `nombre`, `anio` y `previas`. No incorpores notas ni aprobaciones personales al catálogo. Las altas hechas por administradores se guardan en SQLite y no deben reescribir estos archivos.
- **Progreso:** `usuarios` indica el plan activo; `aprobadas` registra la combinación usuario, plan y código. Cambiar de plan no borra aprobaciones y repetir una aprobación no crea otra fila. No versiones `progreso.sqlite3` ni sus archivos auxiliares.
- **Correlativas:** `materias quiensigue` excluye materias ya aprobadas. Una lista de previas vacía habilita la materia; en los demás casos alcanza con cumplir *una* alternativa, pero se deben cumplir *todos* los requisitos dentro de ella. No aplanes las alternativas al modificar el catálogo.

## Cómo verificar un cambio

Desde la raíz, ejecutá `python -m unittest discover -v` (Python 3, sin servicios externos). Agregá pruebas en `correlativas/tests/` con SQLite en memoria. Si cambiás comandos o permisos, cubrí tanto la respuesta esperada como el caso rechazado y actualizá los ejemplos de la guía de uso.

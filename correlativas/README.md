# Bot de correlativas (Python 3)

Desde la raíz del repositorio, probá los comandos sin configurar una plataforma de chat:

```sh
python -m correlativas.bot ana unirse computacion-2024
python -m correlativas.bot ana mostrar anio computacion-2024 1
python -m correlativas.bot ana aprobar materia D1001
python -m correlativas.bot ana materias quiensigue
```

El catálogo deriva de `salida/materias.json` y `salida/correlativas.json` del [MapeadorDeCorrelativas](https://github.com/E1Naiko/MapeadorDeCorrelativas/tree/1c2fb3e6b09c0aad608fcdbd67f08c14789d6d24). No importa notas personales. Las actividades sin año válido no aparecen en el listado por año. `quiensigue` considera requisitos **para cursar**: basta una alternativa completa, una aprobación satisface también una regularización y se cuentan las aprobaciones para los mínimos de actividades. Registrar aprobaciones históricas no exige cargar las previas en orden.

Para conectar un bot existente, importá `Bot` desde `correlativas.bot`, instanciá `Bot(conexion_sqlite)` y enviá al chat el resultado de `responder(id_del_remitente, texto)`. Usá el ID autenticado de la plataforma, no el nombre del chat. El progreso persiste por usuario y plan aunque se cambie de plan activo.

### Administración del catálogo

Configurá `BOT_ADMIN_IDS` en el proceso del bot con los IDs de remitentes autorizados separados por comas (sin configurar, nadie es admin). También podés pasar `admins={...}` al constructor. El argumento `usuario` de la consola es solo para pruebas locales; en un chat no permitas que el remitente elija su ID.

```text
admin agregar plan sistemas-2027
admin agregar materia sistemas-2027 MAT1 1 Matemática I
admin agregar materia sistemas-2027 MAT2 2 Matemática II | MAT1
```

Podés agregar materias a planes nuevos o al plan incluido. Después del `|` van los códigos de **todas** las previas necesarias, separados por comas; omití esa sección si no hay previas. En consola, pasá el mensaje entre comillas si contiene `|`. Las altas persisten en la misma base SQLite que el progreso, sin modificar los JSON originales.

Desde la raíz, ejecutá las pruebas con `python -m unittest discover -v`.

### Almacenamiento local

La consola crea `progreso.sqlite3` en el directorio de trabajo. Ejecutala siempre desde la misma carpeta para reutilizar el progreso y las altas del catálogo. Las pruebas usan bases en memoria y no modifican ese archivo.

Para cambios en el código o en el catálogo inicial, consultá la [guía de mantenimiento del repositorio](../AGENTS.md).

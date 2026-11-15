# Diseño de base de datos

## Alcance

Diseño aprobado e implementado para persistir el tablero Kanban local del MVP en SQLite. El modelo refleja las columnas y tarjetas que hoy existen en `frontend/src/lib/kanban.ts` y permite múltiples usuarios en el futuro, con un único tablero por usuario.

El esquema detallado y legible por máquina está en [database-schema.json](./database-schema.json). El usuario aprobó el modelo antes de implementar esta persistencia.

## Entidades y relaciones

- `users`: identidad de cada usuario, con `id` y `username` único. No guarda contraseñas: el login actual es una simulación frontend y no es una credencial de producción.
- `boards`: pertenece a un usuario. `UNIQUE(user_id)` garantiza un tablero por usuario.
- `columns`: pertenece a un tablero y usa `position` para mantener el orden. El MVP inicia con las cinco columnas de demostración y permite renombrarlas.
- `cards`: pertenece a una columna y usa `position` para ordenar tarjetas. Su `title` y `details` corresponden al modelo del frontend.

Las claves foráneas eliminan en cascada los datos dependientes al borrar usuario, tablero o columna. Cada conexión SQLite activa `PRAGMA foreign_keys = ON`. Las posiciones deben ser no negativas; las escrituras que cambian varias posiciones se hacen dentro de una transacción.

## Persistencia del MVP

- SQLite inicializa la base y las tablas al arrancar si todavía no existen.
- Si no hay tablero para el usuario demo, se crean el tablero, las cinco columnas y las tarjetas que hoy están en `initialData`.
- La lectura ordena columnas y tarjetas por `position` y devuelve la forma `BoardData` (`columns` con `cardIds` y `cards` indexadas por id).
- El reordenamiento cambia la columna y posición de tarjetas en una transacción.

La inicialización está en `backend/app/database.py`; la API se reparte entre `backend/app/api/` y `backend/app/boards.py`, con las acciones de IA en `backend/app/board_updates.py`. En Docker, la base se guarda en el volumen persistente `kanban_data` en `/data/kanban.db`; fuera de Docker, la ruta predeterminada es `backend/data/kanban.db`.

## API disponible

El nombre de usuario en las rutas identifica el tablero demo; no autentica la solicitud. La autenticación sigue siendo solo una simulación frontend.

- `GET /api/boards/usuario`: devuelve el tablero.
- `POST /api/boards/usuario/columns/col-backlog/cards`: crea una tarjeta (`title`, `details` opcional).
- `PATCH /api/boards/usuario/cards/{card_id}`: actualiza parcialmente `title` o `details`.
- `DELETE /api/boards/usuario/cards/{card_id}`: borra una tarjeta.
- `PATCH /api/boards/usuario/columns/{column_id}`: renombra una columna.
- `PUT /api/boards/usuario/cards/order`: recibe `columns`, cada una con `columnId` y la lista ordenada `cardIds`; debe incluir cada columna y cada tarjeta exactamente una vez.

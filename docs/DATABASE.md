# Diseño de base de datos

## Alcance

Propuesta para persistir el tablero Kanban local del MVP en SQLite. El modelo refleja las columnas y tarjetas que hoy existen en `frontend/src/lib/kanban.ts` y permite múltiples usuarios en el futuro, con un único tablero por usuario.

El esquema detallado y legible por máquina está en [database-schema.json](./database-schema.json). Es una propuesta; no se crean todavía la base de datos, tablas ni migraciones hasta que el usuario apruebe el modelo.

## Entidades y relaciones

- `users`: identidad de cada usuario, con `id` y `username` único. No guarda contraseñas: el login actual es una simulación frontend y no es una credencial de producción.
- `boards`: pertenece a un usuario. `UNIQUE(user_id)` garantiza un tablero por usuario.
- `columns`: pertenece a un tablero y usa `position` para mantener el orden. El MVP inicia con las cinco columnas de demostración y permite renombrarlas.
- `cards`: pertenece a una columna y usa `position` para ordenar tarjetas. Su `title` y `details` corresponden al modelo del frontend.

Las claves foráneas eliminan en cascada los datos dependientes al borrar usuario, tablero o columna. Se habilitará `PRAGMA foreign_keys = ON` en cada conexión SQLite. Las posiciones deben ser no negativas; las escrituras que cambien varias posiciones se harán dentro de una transacción.

## Persistencia propuesta para el MVP

- Usar un archivo SQLite local dentro del volumen persistente del contenedor.
- Crear la base y las tablas automáticamente si todavía no existen.
- Al inicializar la cuenta demo si no hay tablero, crear el tablero, las cinco columnas y las tarjetas de ejemplo que hoy están en `initialData`.
- Leer el tablero ordenando columnas y tarjetas por `position` y devolver al frontend la forma `BoardData` (`columns` con `cardIds` y `cards` indexadas por id).
- Para mover tarjetas entre columnas, actualizar su `column_id` y `position` dentro de una transacción.

La inicialización y la API pertenecen a la fase 6; aquí solo se documenta el diseño para aprobación.

## Decisiones pendientes de aprobación

1. Aprobar las cuatro tablas `users`, `boards`, `columns` y `cards`, incluyendo un tablero por usuario.
2. Aprobar el uso de posiciones enteras para ordenar columnas y tarjetas.
3. Aprobar no persistir contraseña en SQLite mientras la autenticación sea únicamente simulada en frontend.

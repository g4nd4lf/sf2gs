## Estrategia para eliminar duplicados:

He comprobado que sqlite3 da problemas para eliminar duplicados cuando trata con campos que tienen muchos decimales como Js o Js_vpd

En el caso de las tablas _tzs_Jsvpd la forma más sencilla de eliminar duplicados es eliminar simplmente las tablas que tengan identicos valores de timestamp, arbol y sup, como:
```
DELETE FROM CR6Irriwell4_tzs_Jsvpd
        WHERE ROWID NOT IN (
            SELECT MIN(ROWID)
            FROM CR6Irriwell4_tzs_Jsvpd
            GROUP BY timestamp, arbol, sup);
```
Antes intentaba usar una fórmula genérica para eliminar duplicados:
```
DELETE FROM {table}
        WHERE ROWID NOT IN (
            SELECT MIN(ROWID)
            FROM {table}
            GROUP BY {', '.join(campos)}
        );

Donde campos incluia todas las columnas de la tabla
```
pero la fórmula genérica falla cuando alguna columna tiene datos con muchsos decimales.

Una solución mejor sería definir una primary_key que séa única para cada registro uniendo esos campos: PRIMARY_KEY= timestamp_arbol_sup así se haría imposible ingresar valores duplicados y no habria que eliminarlos.
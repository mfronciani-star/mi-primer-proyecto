# Entrega práctica 4 — Streaming

Nombre: Maximiliano Fronciani

student_id: maxi_fronciani

Escala: small

## Log y offsets

1- Despues de leer tres mensajes, en la cola quedaron 2 (pago_4 y pago_5) y en el log siguieron estando los 5, con el offset del consumidor en 3. En una cola tradicional el mensaje se borra cuando alguien lo lee, asi que lo consume un solo lector y no se puede volver a leer. En un log como Kafka los mensajes se conservan y cada consumidor solo guarda hasta donde leyo (su offset), por eso varios consumidores pueden leer los mismos mensajes a su ritmo y se puede volver a leer desde el principio.

2- Despues de la llegada 2, el consumidor antifraude habia leido 180 mensajes (60 en la llegada 1 y 120 en la 2) y el de reportes 0. El atraso de reportes no afecto a antifraude, que siguio leyendo al dia. Cada consumidor lee el log a su propio ritmo y guarda su propia posicion, asi que uno lento solo se atrasa a si mismo. Reportes se puso al dia de una vez en la llegada 3, leyendo los 220 mensajes pendientes.

3- Un offset es la posicion dentro del log hasta donde un consumidor ya leyo: le dice desde donde seguir la proxima vez. En esta practica cada consumidor guarda su offset en su propio checkpoint, una carpeta en el volumen (landing/streaming_lab/...) que Structured Streaming actualiza al terminar cada lectura. Como cada consumidor tiene un checkpoint distinto, cada uno avanza por separado sobre el mismo topic.

4- El replay leyo los 280 mensajes, todos los que tiene el topic, porque arranco con un checkpoint nuevo y leyo desde el inicio. La arquitectura Kappa propone reprocesar volviendo a leer el log completo con la logica nueva, usando un solo pipeline de streaming. Lambda, en cambio, mantiene dos caminos separados, uno batch para reprocesar y otro de streaming para lo reciente, lo que obliga a escribir y mantener la misma logica dos veces.

## Ingesta y enriquecimiento

5- Bronze proceso 60 filas en la llegada 1, 120 en la 2, 40 en la 3, 40 en la 4 y 20 en la 5, las mismas que tenia cada archivo. Al reejecutar sin archivos nuevos proceso 0 filas, tanto en Bronze como en Silver. Lo que evita leer dos veces el mismo archivo es el checkpoint de Auto Loader, que registra que archivos ya se procesaron y en la siguiente ejecucion solo toma los nuevos.

6- Aparecieron dos motivos de rechazo, los dos en la llegada stream_002: INVALID_AMOUNT (20 registros) y UNKNOWN_CUSTOMER (20 registros), que son las 40 filas en cuarentena de esa llegada. Bronze guarda el texto original en vez de descartar los errores para no perder informacion: asi se puede ver que llego exactamente, investigar el problema con la fuente y, si se corrige la regla, volver a procesar los datos sin pedirlos de nuevo.

7- El join agrego la columna country (desde silver_customers) y la columna category (desde silver_products), porque los eventos llegaron solo con customer_id y product_id. Es un join stream-tabla: de un lado esta el flujo de eventos que va llegando y del otro una tabla de referencia fija. Cada evento nuevo se completa con los datos de esa tabla, y si el customer_id no existe en silver_customers el evento queda en cuarentena como UNKNOWN_CUSTOMER.

## Tiempo y ventanas

8- El event time es el momento en que ocurrio la compra y el processing time es el momento en que el sistema la recibe. late_ok tiene event time 12:03, pero llego recien en la llegada 2, junto con compras de 12:06 y 12:08. Si se agrupara por processing time quedaria con las compras de la llegada 2; agrupando por event time se cuenta en la ventana [12:00, 12:05), que es donde realmente ocurrio.

9- Al terminar cada llegada el watermark valia 11:54, 11:58, 12:16, 12:17 y 12:35. Se calcula como el maximo event time visto menos 10 minutos de tolerancia: por ejemplo, en la llegada 3 el maximo fue 12:26, asi que el watermark quedo en 12:16.

10- Las primeras ventanas tumbling en modo append aparecieron en la llegada 3 (4 ventanas). En modo append una ventana se emite solo cuando ya esta cerrada, es decir cuando el watermark pasa su hora de fin. Despues de la llegada 2 el watermark era 11:58, todavia antes del fin de la primera ventana (12:05). En la llegada 3 subio a 12:16 y cerro las ventanas [12:00, 12:05) y [12:05, 12:10).

11- late_bad se descarto: tiene event time 12:02 y llego en la llegada 4, cuando el watermark ya estaba en 12:16, y aparecen 20 eventos mas viejos que el watermark (las 20 repeticiones de late_bad). late_ok se acepto porque, aunque llego tarde, su event time (12:03) todavia estaba dentro de la tolerancia: el watermark era 11:54 y su ventana seguia abierta. late_bad llego cuando su ventana ya se habia cerrado.

12- Tumbling usa ventanas fijas de 5 minutos que no se superponen, asi que cada compra cae en una sola (80, 40 y 60 compras). Ejemplo: ventas cada 5 minutos para un tablero. Hopping usa ventanas de 10 minutos que avanzan cada 5, se superponen y cada compra cuenta en dos ventanas. Ejemplo: ventas de los ultimos 10 minutos actualizadas cada 5, para detectar picos. Session no tiene duracion fija: agrupa las compras de cada cliente y se cierra despues de 5 minutos sin actividad (el cliente 0 tuvo una sesion de 4 compras y otra de 3). Ejemplo: analizar cada visita de un usuario a la tienda.

13- En modo update la ventana [12:00, 12:05) de card se emitio dos veces: en la llegada 1 con 40 compras y 6.000, y en la llegada 2 con 60 compras y 8.400 (ya con late_ok incluido). En modo append se emitio una sola vez, en la llegada 3, con el valor final de 60 compras y 8.400. Update da resultados antes, pero los valores cambian y quien los recibe tiene que reemplazarlos. Append emite cada ventana una sola vez y con el valor definitivo, pero hay que esperar a que el watermark la cierre.

14- Con un watermark de 1 minuto las ventanas se cerrarian mucho antes, asi que los resultados en modo append saldrian con menos demora y habria que guardar menos estado. A cambio se tolerarian muchos menos datos tardios: eventos como late_ok, que llego varios minutos despues, tendrian mas riesgo de descartarse y los totales quedarian incompletos.

## Garantias y fallas

15- Sin deduplicar quedaron 220 filas en el destino y deduplicando por event_id quedaron 200. La diferencia son los eventos repetidos, como e002_000, que llego en stream_001 y de nuevo en stream_002. El productor puede enviar el mismo evento dos veces porque, si no recibe la confirmacion de que el mensaje llego (por ejemplo por un corte de red o un timeout), lo reintenta, aunque el primero si se haya guardado.

16- Al reiniciar con el mismo checkpoint el destino siguio con 200 filas: el checkpoint recordaba hasta donde se habia procesado, asi que no volvio a escribir nada. Ahi se observa exactly-once, cada evento queda una sola vez. Al perder el checkpoint y escribir con append, el destino paso a 400 filas, porque la consulta no sabia que ya habia procesado todo y volvio a escribir los mismos eventos. Ahi se observa at-least-once: no se pierde nada, pero puede haber duplicados.

17- Con MERGE quedaron 200 filas tanto en la primera ejecucion como despues de perder el checkpoint. MERGE busca cada evento por event_id en el destino: si ya existe lo actualiza (o lo deja igual) y solo inserta los que no estan, entonces reprocesar los mismos datos no agrega filas. Que una escritura sea idempotente significa que aplicarla una o varias veces deja el mismo resultado, y por eso se puede reintentar sin miedo a duplicar.

## CDC

18- El log genero 13 eventos de cambio: 6 insert (los 5 clientes iniciales y el cliente 100), 3 update_preimage, 3 update_postimage (por los 3 UPDATE) y 1 delete (el cliente 3). Un UPDATE genera dos eventos porque el log guarda la fila antes del cambio (update_preimage) y la fila despues (update_postimage). Asi quien consume el log sabe que valor tenia y cual tiene ahora, por ejemplo que el cliente 1 paso de segmento new a premium.

19- Si, la tabla reconstruida a partir del log quedo igual a la tabla actual: los clientes 0, 1, 2, 4 y 100 con los mismos datos. El log tiene ademas la historia que la tabla actual no tiene: los valores anteriores, el momento y la version de cada cambio, y los registros borrados. Por ejemplo, en la tabla actual el cliente 2 figura en BR, pero el log muestra que estuvo en UY (version 0), despues en CL (version 3) y recien en la version 8 paso a BR. Tambien muestra que el cliente 3 existio y fue borrado en la version 5.

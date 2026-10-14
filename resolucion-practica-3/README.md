# Entrega práctica 3 — Bases de datos NoSQL

Nombre: Maximiliano Fronciani

student_id: maxi_fronciani

Escala: small

Respondé cada pregunta en una a tres oraciones. Cuando se pide un dato, copiá el valor que te dio el notebook.

CAP y PACELC

1- CP rechaza las operaciones en C porque quedó aislada y no puede garantizar el dato correcto. Sacrifica la disponibilidad.

AP responde igual, pero C devuelve 100, un valor viejo (el saldo real ya era 80 por la compra en A). Sacrifica la consistencia.

2- En modo AP, después de la reparación (last-write-wins) las tres réplicas quedaron con saldo 50. Se perdió la escritura de saldo=80, la compra que se hizo en A: como la escritura en C fue la última, pisó a la otra.

3- p99 con w=1 es 9,6ms y el p99 con w=3 es 55,6. Se gana consistencia: cuando la escritura se confirma, ya está en todas las réplicas y cualquier lectura devuelve el dato nuevo.

4- ABC pudo seguir escribiendo: write saldo=80 vía A → OK, y quedó en 80 en A, B y C.

DE no: write saldo=50 vía D → ERROR: sin quórum, y leer en E también dio error. D y E se quedaron en 100.

Es porque en modo CP se necesita mayoría: con 5 réplicas, el quórum es 3. ABC tiene 3 y lo alcanza; DE tiene 2 y no. Así se garantiza que nunca escriban los dos lados a la vez, porque solo uno puede tener mayoría.

Clave-valor

5-  El GET en memoria tardó 0,0002 ms y el GET con Spark sobre Delta 556 ms: el de memoria fue unas 2.756.522 veces más rápido.

Redis guarda los datos en memoria porque la RAM es muchísimo más rápida que el disco, y está pensado para responder en microsegundos (cachés, sesiones, carritos). Spark, en cambio, tiene que levantar una consulta distribuida y leer archivos Delta, lo que tiene un costo fijo enorme para buscar una sola clave. La contra de la memoria es que es más cara y limitada, y si el servidor se cae hace falta persistencia o réplicas.

6- Se encontraron 992 clientes de AR, pero para eso hubo que parsear los 5.000 valores. En clave-valor la base solo conoce la clave (customer:42); el valor es un JSON que no entiende, así que no puede filtrar por country. Hay que traer todo y filtrar afuera.

Ventaja: el acceso por clave es rapidísimo y simple (GET customer:42 devuelve el perfil completo de una).

Desventaja: no sirve para consultas por contenido; cualquier filtro o conteo obliga a recorrer todos los valores.

7- Hash modo N 79,6%.

Hashing consistente 21,2%.

Conviene el hashing consistente porque, al agregar un nodo, solo se mueven las claves que pasan al nodo nuevo (lo ideal es 1/5 = 20%), y no casi todas. Eso significa mucho menos tráfico y menos tiempo de rebalanceo.

Documental

8- La consulta relacional uso 3 tablas y 2 joins y devolvio 11 filas, una por transaccion, repitiendo los datos del cliente en cada una. La documental devolvio 1 documento sin joins. Dentro del documento quedaron embebidos el perfil del cliente (pais, segmento, fecha de alta, email), sus estadisticas (11 transacciones, 9.379,80 de monto, 1 fraude) y el array con sus 11 transacciones, cada una con su producto adentro (id, categoria y precio).

9- Spark armo un unico esquema con todos los campos que aparecen en algun documento (loyalty, phones, preferences, profile, schema_version) y a los documentos que no traen un campo se lo completo con null. Por ejemplo, el 900002 no trae el campo email y quedo en null, y el 900003 lo trae pero vacio. Se dice que tiene esquema flexible porque cada documento puede tener campos distintos sin que la base lo rechace: no hay que definir columnas antes ni modificar la tabla para agregar algo nuevo. La contra es que la aplicacion tiene que manejar los campos que faltan.

10- El documento mas grande pesa 5,2 KB, unos 225 bytes por transaccion. Si un documento crece sin limite llega al tamaño maximo (en MongoDB 16 MB, que a este ritmo serian unas 74.599 transacciones) y no se puede seguir escribiendo. Ademas se vuelve lento, porque cada lectura trae el documento entero y cada compra nueva obliga a reescribirlo completo. Para evitarlo se guardan las transacciones en otra coleccion con referencia al cliente, o se embeben solo las ultimas.

11- Hubo que usar explode porque las transacciones estan dentro de un array en cada cliente, y para agrupar por categoria hay que desarmar los arrays y convertir cada transaccion en una fila. El resultado fue books 11.165.281,86, home 11.142.997,14, sports 10.011.643,20, fashion 9.085.335,88 y electronics 9.025.940,25. El modelo documental resuelve bien las consultas centradas en el cliente, como traer todo del cliente 42 en una sola lectura. Le cuestan mas las que cruzan documentos o miran los datos por otro eje, como el monto por categoria o las ventas por producto, porque hay que abrir todos los documentos y reagrupar.

Grafos

12- El grafo tiene 5.000 nodos Customer (738 de ellos marcados), 2.361 nodos Device y aproximadamente 5.400 aristas USES. Cada arista une a un cliente con un dispositivo que uso. La mayoria de los clientes usa un solo dispositivo y unos 400 usan dos, mientras que un mismo dispositivo puede estar compartido por hasta 8 clientes.

13- Para el patron de 2 saltos (cliente - dispositivo - otro cliente) SQL necesito 3 joins y alcanzo 1.389 clientes. Para el de 4 saltos necesito 5 joins y alcanzo 254 clientes. En SQL cada salto es un join mas, que tiene que buscar coincidencias entre tablas enteras, y el costo crece con cada salto. Neo4j guarda en cada nodo las referencias directas a sus relaciones (adyacencia sin indices), entonces pasar de un nodo a su vecino es seguir un puntero, sin buscar en toda la tabla. Por eso recorrer relaciones de varios saltos es mucho mas eficiente.

14- Tardo 14 iteraciones en converger: en la iteracion 14 ya no cambio ningun nodo de componente. En las dos primeras cambiaron miles de nodos (2.361 y 2.931) y despues fue bajando hasta 0. Cada iteracion equivale a un salto mas en el grafo. El componente mas grande tiene 23 nodos y 22 aristas.

15- Con hash(id) mod 4 el 74,4% de las aristas quedo entre maquinas distintas. Repartiendo por componente quedo en 0%, con una carga parecida en las cuatro maquinas. Es dificil distribuir una base de grafos porque los datos estan conectados entre si: si se reparten los nodos sin mirar sus relaciones, casi todos los recorridos tienen que saltar de una maquina a otra por la red, que es mucho mas lento. Repartir para cortar pocas aristas y a la vez dejar la carga equilibrada entre maquinas es un problema complicado, y en grafos reales no suele haber componentes tan separados como en este caso.

Vectorial

16 - El vector de cada cliente es un resumen numerico de como compra, con 10 dimensiones: la proporcion de compras en cada categoria (electronics, home, books, sports, fashion), la proporcion de uso de cada canal de pago (card, wallet, transfer), el monto promedio normalizado y la proporcion de compras de ticket alto. Dos clientes con vectores parecidos tienen habitos de compra parecidos. La similitud coseno mide el angulo entre dos vectores: si apuntan en la misma direccion da cerca de 1 (perfiles muy parecidos) y si no tienen nada que ver da cerca de 0. Por ejemplo, el vecino mas cercano del cliente 13 tuvo una similitud de 0,973.

17 - Entre los 10 vecinos mas parecidos de los clientes marcados hay un 31,6% de marcados, contra una tasa base de 14,8% (y 13,2% entre los vecinos de clientes no marcados). O sea que los marcados se parecen entre si: tener un vecino marcado duplica la probabilidad de estar marcado. Buscar vecinos parecidos sirve para encontrar clientes con un comportamiento similar a casos conocidos, por ejemplo para priorizar a quien revisar por fraude o para recomendar productos. Igual hay que tener cuidado: el clasificador k-NN tuvo 85,9% de exactitud, menos que predecir siempre "no marcado" (86,3%), asi que sirve como señal para investigar pero no como clasificador por si solo.

18 - Con nprobe=4 se obtiene un recall de 0,872 (encuentra el 87,2% de los 10 vecinos reales) escaneando solo el 6% de los vectores. Con la busqueda aproximada se gana velocidad, porque se compara contra una parte chica de los datos en vez de contra todos. Se pierde exactitud, porque se pueden escapar vecinos que estaban en clusters que no se revisaron. Subiendo nprobe se mejora el recall a cambio de mas trabajo: con nprobe=8 llega a 0,966 escaneando el 12% y con nprobe=16 llega a 1 escaneando el 24%.

Columnar

19- Las 503.490 transacciones ocupan 50,0 MB en CSV, 121,1 MB en JSON y 5,3 MB en Parquet, o sea que Parquet ocupa 9,4 veces menos que CSV y 22,8 veces menos que JSON. Para la consulta de amount sobre Parquet, Spark leyo una sola columna: ReadSchema: `struct<amount:decimal(12,2)>`, mientras que para la consulta sobre todas las columnas leyo las 10. Con los datos ordenados por amount se pueden saltear 7 de 8 archivos para el filtro amount > 1900, porque el minimo y maximo de cada archivo ya indican que no tiene filas que cumplan. Con los datos al azar no se puede saltear ninguno.

20- El formato columnar guarda juntos todos los valores de una misma columna. Para analitica es muy bueno porque las consultas suelen usar pocas columnas sobre muchas filas: se leen solo las columnas necesarias, los valores parecidos se comprimen mucho mejor y con las estadisticas de cada archivo (minimo y maximo) se pueden saltear archivos enteros. En cambio, para modificar una fila por vez es poco conveniente, porque los datos de esa fila estan repartidos en todas las columnas y los archivos Parquet no se editan en el lugar: hay que reescribir el archivo completo (en Delta se marca el archivo viejo como borrado y se escribe uno nuevo).

# Entrega práctica 5 — MLOps con MLflow

Nombre: Maximiliano Fronciani

student_id: maxi_fronciani

Escala: small

## Mis runs

| run | modelo | features | class_weight | umbral | hiperparametros | train_pr_auc | pr_auc | accuracy | precision | recall | f1 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| boosting_completas_u03 | gradient_boosting | completas | balanced | 0.3 | learning_rate=0.1, max_depth=3 | 0.602 | 0.586 | 0.698 | 0.243 | 0.9 | 0.382 |
| bosting completas_balanced | gradient_boosting | completas | balanced | 0.5 | learning_rate=0.1, max_depth=3 | 0.602 | 0.586 | 0.809 | 0.329 | 0.808 | 0.468 |
| boosting_completas_u03 | gradient_boosting | completas | ninguno | 0.3 | learning_rate=0.1, max_depth=3 | 0.608 | 0.585 | 0.908 | 0.554 | 0.564 | 0.559 |
| boosting_completas. | gradient_boosting | completas | ninguno | 0.5 | learning_rate=0.1, max_depth=3 | 0.608 | 0.585 | 0.918 | 0.717 | 0.353 | 0.473 |
| max_depth=8 | random_forest | completas | ninguno | 0.5 | n_estimators=100, max_depth=8 | 0.643 | 0.568 | 0.914 | 0.799 | 0.226 | 0.352 |
| forest_compeltas | random_forest | completas | ninguno | 0.5 | n_estimators=100, max_depth=8 | 0.643 | 0.568 | 0.914 | 0.799 | 0.226 | 0.352 |
| Logistica completa | logistic_regression | completas | ninguno | 0.5 | C=0.1 | 0.531 | 0.545 | 0.916 | 0.756 | 0.277 | 0.406 |
| max_depth=5 | random_forest | completas | ninguno | 0.5 | n_estimators=100, max_depth=5 | 0.561 | 0.541 | 0.903 | 0.906 | 0.078 | 0.144 |
| max_depth=sin_limite | random_forest | completas | ninguno | 0.5 | n_estimators=100, max_depth=sin_limite | 1.0 | 0.537 | 0.916 | 0.689 | 0.341 | 0.456 |
| max_depth=3 | random_forest | completas | ninguno | 0.5 | n_estimators=100, max_depth=3 | 0.535 | 0.525 | 0.896 | 0.0 | 0.0 | 0.0 |
| max_depth | random_forest | completas | ninguno | 0.5 | n_estimators=100, max_depth=3 | 0.535 | 0.525 | 0.896 | 0.0 | 0.0 | 0.0 |
| max_depth | random_forest | completas | ninguno | 0.5 | n_estimators=100, max_depth=3 | 0.535 | 0.525 | 0.896 | 0.0 | 0.0 | 0.0 |
| 01_repro_b | random_forest | cliente | ninguno | 0.5 | n_estimators=100, max_depth=8 | 0.594 | 0.51 | 0.909 | 0.722 | 0.207 | 0.321 |
| 01_repro_a | random_forest | cliente | ninguno | 0.5 | n_estimators=100, max_depth=8 | 0.594 | 0.51 | 0.909 | 0.722 | 0.207 | 0.321 |
| Logistica cliente | logistic_regression | cliente | ninguno | 0.5 | C=0.1 | 0.447 | 0.448 | 0.902 | 0.609 | 0.151 | 0.242 |

Run registrado: boosting_completas_u03 (gradient_boosting con completas, class_weight balanced y umbral 0.3), versión 3 de workspace.bigdata_maxi_fronciani.fraud_model con alias champion.

## Datos y tracking

1- Train tiene 35.654 filas con 11,05% de contracargos, test 7.129 con 10,38% y nuevas 7.165 con 11,05%. Se separa por fecha porque así funciona en la realidad: el modelo se entrena con el pasado y se usa sobre lo que viene después. Si se separara al azar el modelo vería datos "del futuro" al entrenar y las métricas darían mejor de lo que darían en producción.

2- Decir siempre que no hay contracargo da una accuracy de 89,6%, sin detectar ni un solo contracargo. Como las clases están desbalanceadas la accuracy engaña. El PR-AUC mide qué tan bien el modelo ordena las transacciones de más a menos riesgosas, se enfoca en la clase positiva y no depende del umbral. Un modelo al azar tiene un PR-AUC igual a la tasa de contracargos, 0,104.

3- Como parámetros quedaron model_type logistic_regression, feature_set basicas, C 1.0, class_weight ninguno, threshold 0.5, data_table ml_features y data_version. Como métricas quedaron test_pr_auc 0,339, roc_auc 0,794, accuracy 0,896, precision 0,493, recall 0,045, f1 0,082, 67 alertas y train_pr_auc 0,341. Como artefacto quedó la matriz de confusión, y el modelo con su firma aparece en Logged models. Un experimento es la carpeta que agrupa los entrenamientos de un mismo problema y un run es cada entrenamiento dentro de él.

4- Autolog registró 46 parámetros. Sus métricas son todas de entrenamiento: training_accuracy 0,91, f1 0,887, log_loss 0,229, precision 0,901, recall 0,91, roc_auc 0,899 y score 0,91. No registra las métricas sobre test, ni el PR-AUC, ni el umbral, ni la versión de los datos, que sí registramos a mano.

5- Sí, dieron exactamente las mismas métricas (PR-AUC 0,51 en los dos). Para que un run sea reproducible hay que fijar los datos, el código, la semilla (random_state=42) y el entorno.

6- MLflow rechazó la predicción con el error "Failed to enforce schema" antes de calcular nada. La firma declara qué columnas y tipos espera el modelo (amount double y payment_channel string) y qué devuelve, así que funciona como un contrato que frena los datos que no lo cumplen.

## Tus experimentos

7- Mi mejor run fue gradient boosting con completas, learning_rate 0.1 y max_depth 3, con un PR-AUC de 0,586 (la versión con class_weight balanced; sin balanced dio 0,585). Usando solo rule_alert el PR-AUC fue 0,17, así que el modelo más que triplica a la regla. Además la regla sola con umbral 0,5 no generó ninguna alerta.

8- Con la regresión logística el PR-AUC pasó de 0,339 con basicas a 0,448 con cliente y a 0,545 con completas, así que cada grupo de variables suma bastante. En el mejor run las variables más importantes fueron amount (0,327), payment_channel (0,175), hour (0,103) y category (0,074). 

9- Con completas el mejor fue el boosting (0,585), después el bosque (0,568) y por último la logística (0,545). Un modelo de random forest va partiendo los datos en ramas, entonces puede aprender reglas como "de noche y por transferencia el riesgo sube" sin que nadie le arme esa combinación. La logística suma el efecto de cada variable por separado, así que una combinación así solo la ve si se le agrega como variable nueva.

10- Con balanced el boosting pasó de precision 0,717 y recall 0,353 a precision 0,329 y recall 0,808, y las alertas subieron a 1.818 (cerca de un cuarto de las transacciones de test). Detecta muchos más contracargos pero con muchas más alertas falsas. El PR-AUC casi no cambió (0,585 contra 0,586).

11- Al bajar el umbral de 0,5 a 0,3 en el boosting las alertas subieron a 753, el recall pasó de 0,353 a 0,564 y la precision bajó de 0,717 a 0,554. El PR-AUC quedó igual (0,585). El PR-AUC mide cómo ordena el modelo el riesgo considerando todos los umbrales posibles, mientras que el F1 se calcula con las alertas de un umbral en particular, por eso cambia (de 0,473 a 0,559).

12- Barrí max_depth en un random forest con completas. El mejor PR-AUC de test fue con max_depth 8 (0,568); con 3 dio 0,525 y con 5 dio 0,541. Sin límite el PR-AUC de train llegó a 1 pero el de test bajó a 0,537. Eso es sobreajuste: el modelo memoriza los datos de entrenamiento en lugar de aprender patrones que se repitan.

## Comparar y elegir

13- No coincidieron. El mejor por PR-AUC fue boosting_completas_u03 (0,586, con accuracy 0,698) y el mejor por accuracy fue boosting_completas con umbral 0,5 (0,918). Pueden no coincidir porque la accuracy premia alertar poco: con 10% de contracargos, un modelo que alerta poco acierta casi siempre aunque deje pasar muchos fraudes. Un umbral bajo o balanced genera más alertas y baja la accuracy aunque el modelo ordene igual de bien.

14- El que queda más lejos de la diagonal es max_depth=sin_limite, con PR-AUC 1 en train y 0,537 en test. Eso indica sobreajuste. El resto queda cerca de la diagonal, con diferencias de 0,01 a 0,08.

15- Con search_runs los runs se pueden filtrar y ordenar desde código como una tabla, así que se pueden automatizar comparaciones y elegir el mejor sin mirarlos uno por uno. Para traer solo mis bosques con PR-AUC de test mayor a 0,55 usaría: tags.student_id = 'maxi_fronciani' AND params.model_type = 'random_forest' AND metrics.test_pr_auc > 0.55

16- Cuesta más un contracargo no detectado, porque la plataforma pierde la plata de la compra; una alerta falsa solo cuesta el tiempo de revisarla y alguna molestia al cliente. Si el equipo puede revisar una cantidad fija de alertas por día, ordenaría las transacciones por score y elegiría el umbral que genere aproximadamente esa cantidad, así revisan siempre las más riesgosas.

## Registro, uso y monitoreo

17- Sí, se registró como workspace.bigdata_maxi_fronciani.fraud_model, versión 3, con alias champion (las versiones 1 y 2 quedaron de pruebas anteriores). Cargar models:/...@champion permite cambiar de modelo moviendo el alias a otra versión, sin tocar el código que lo usa. Con runs:/<run_id>/model habría que cambiar el código cada vez que se elige otro modelo.

18- Se puntuaron 7.165 transacciones y 2.741 generaron alerta (38,3%). Son muchas porque el champion usa balanced y umbral 0,3. Para auditar cada decisión están score, alerta, threshold, model_name, model_version, run_id y scored_at. El umbral se guarda fuera del modelo porque es una decisión de negocio que depende de cuántas alertas se pueden revisar, y así se puede cambiar sin reentrenar.

19- Sí, el PR-AUC sobre nuevas fue 0,579 contra 0,586 en test, muy parecido. Con la campaña simulada las alertas pasaron de 38,3% a 56,7%, porque subió el importe promedio (de 989 a 1.218) y las transferencias (de 33% a 61%). El drift es cuando los datos que llegan cambian respecto de los de entrenamiento. Se puede detectar antes de tener las etiquetas mirando las distribuciones de las variables de entrada y de los scores, que se conocen en el momento.

## Cierre

20- Datos: armé ml_features con un split temporal. Entrenamiento: probé tres modelos, cuatro conjuntos de variables y un barrido. Tracking: todo quedó registrado en MLflow. Registro: el mejor quedó en Unity Catalog con alias champion. Despliegue: lo usé en inferencia batch sobre las transacciones nuevas. Monitoreo: comparé las métricas con las de test y simulé drift. Para tenerlo en producción real faltaría programar el scoring como un job que corra solo todos los días, tener alertas automáticas cuando cambien las distribuciones o caigan las métricas, reentrenar periódicamente con datos nuevos y elegir el umbral según la capacidad real del equipo de riesgo.

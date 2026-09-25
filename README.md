*This project has been created as part of the 42 curriculum by crblanco, sperez-l.*

# A-Maze-ing

## Descripción

A-Maze-ing es un generador de laberintos en Python. Lee un archivo de configuración, genera el laberinto, lo guarda en un archivo con las paredes codificadas en hexadecimal y lo muestra en la terminal con un pequeño menú interactivo.

Cada laberinto lleva dibujado un "42" en el centro (si el tamaño lo permite), tiene siempre un camino entre la entrada y la salida, y el programa calcula y muestra el camino más corto.

El generador vive en su propio paquete (`mazegen`), separado de la parte visual (`ui`), para poder reutilizarlo en otros proyectos.

## Instrucciones

Necesitas Python 3.12 o superior y [uv](https://docs.astral.sh/uv/).

```bash
make install   # instala dependencias (pydantic + herramientas de desarrollo)
make run       # ejecuta con config.txt
make test      # pasa los tests con pytest
make lint      # flake8 + mypy
make package   # genera mazegen-*.whl en la raíz
make clean     # borra cachés
```

También se puede ejecutar a mano:

```bash
python3 a_maze_ing.py config.txt
```

### Menú

| Opción | Qué hace |
|---|---|
| 1 | Genera un laberinto nuevo. Vuelve a leer el `config.txt`, así que puedes cambiarlo sin cerrar el programa |
| 2 | Muestra u oculta el camino más corto |
| 3 | Cambia al azar los colores y el estilo de las paredes |
| 4 | Sale |

## Archivo de configuración

Una clave por línea con formato `CLAVE=VALOR`. Las líneas que empiezan por `#` son comentarios (no se permiten comentarios al final de una línea).

| Clave | Obligatoria | Descripción | Ejemplo |
|---|---|---|---|
| `WIDTH` | Sí | Ancho en celdas | `20` |
| `HEIGHT` | Sí | Alto en celdas | `15` |
| `ENTRY` | Sí | Entrada, en formato `x,y` | `0,0` |
| `EXIT` | Sí | Salida, en formato `x,y` | `19,14` |
| `OUTPUT_FILE` | Sí | Archivo donde se guarda el laberinto | `maze.txt` |
| `PERFECT` | Sí | `True`: un único camino posible. `False`: con bucles | `True` |
| `SEED` | No | Semilla para repetir el mismo laberinto | `42` |
| `PATH_DELAY` | No | Segundos por celda en la animación del camino (0 a 1, `0` la desactiva). Por defecto `0.03` | `0.05` |

```
# config.txt
WIDTH=20
HEIGHT=15
ENTRY=0,0
EXIT=19,14
OUTPUT_FILE=maze.txt
PERFECT=True
SEED=42
```

Cosas a tener en cuenta:
- La entrada y la salida tienen que estar dentro del laberinto y ser distintas.
- El "42" ocupa 11x7 celdas en el centro. Si la entrada o la salida caen encima, da error. Lo más seguro es ponerlas en los bordes.
- Si el laberinto es más pequeño que 11x7, no se dibuja el "42" y sale un aviso.

### Archivo de salida

Una línea por fila del laberinto, con un dígito hexadecimal por celda. Cada bit indica si esa pared está cerrada: norte = 1, este = 2, sur = 4, oeste = 8 (por ejemplo, `f` es una celda cerrada por los cuatro lados). Después va una línea vacía, la entrada, la salida y el camino más corto con las letras `N`, `E`, `S`, `W`.

## Algoritmo

Usamos **recursive backtracker** (búsqueda en profundidad, DFS), en versión iterativa con una pila para no chocar con el límite de recursión de Python:

1. Se empieza en una celda y se marca como visitada.
2. Se elige al azar un vecino no visitado, se abre la pared entre los dos y se avanza.
3. Si no quedan vecinos libres, se retrocede en la pila hasta encontrar una celda que sí tenga.

Las celdas del "42" se marcan como reservadas y el algoritmo no pasa por ellas.

El resultado es un laberinto perfecto (un solo camino entre dos celdas cualquiera). Con `PERFECT=False` se abren algunas paredes más para crear bucles y se reducen los callejones sin salida. El camino más corto se calcula con BFS.

### Por qué este algoritmo

- Es fácil de entender y de explicar, y de implementar bien.
- Genera pasillos largos y con muchas curvas, que quedan bien visualmente.
- Siempre da un laberinto perfecto, que es justo lo que pide el modo `PERFECT=True`.
- Con una semilla fija el resultado siempre es el mismo, lo que ayuda mucho con los tests.

## Código reutilizable

Todo lo que es generar laberintos está en el paquete `mazegen`, que no depende de la terminal ni del archivo de configuración:

```python
from mazegen import MazeGenerator, MazeOptions, Position

options = MazeOptions(
    width=20,
    height=15,
    entry=Position(0, 0),
    exit=Position(19, 14),
    perfect=True,
    seed=42,
)
result = MazeGenerator().generate(options)

result.grid            # cuadrícula con las paredes de cada celda
result.shortest_path   # por ejemplo "EESSW..."
```

El algoritmo y el modo (perfecto o con bucles) se pueden cambiar pasando otra estrategia a `MazeGenerator`, sin tocar el resto del código. `mazegen.encoder` también se puede usar por separado para exportar la cuadrícula en hexadecimal.

### Generar el paquete

El paquete se genera con `uv build` desde la raíz del repo. No hace falta instalar nada: uv descarga lo necesario para construirlo en un entorno temporal.

```bash
uv build --wheel --out-dir .    # genera mazegen-0.1.0-py3-none-any.whl
uv build --sdist --out-dir .    # genera mazegen-0.1.0.tar.gz
```

- `--wheel` crea el `.whl`, el formato que pip instala directamente.
- `--sdist` crea el `.tar.gz`, que contiene el código fuente del paquete.
- `--out-dir .` deja el archivo en la raíz del repo (si no, iría a `dist/`).

`make package` hace lo mismo que la primera línea y además borra antes el `.whl` anterior.

### Ver qué hay dentro

Los dos archivos son comprimidos, así que se puede ver su contenido sin instalarlos:

```bash
unzip -l mazegen-0.1.0-py3-none-any.whl    # el .whl es un .zip
tar -tzf mazegen-0.1.0.tar.gz              # lista el contenido del .tar.gz
```

`tar -tzf` solo **muestra** la lista de archivos, no extrae nada. Para descomprimirlo de verdad se cambia la `t` por una `x`:

```bash
tar -xzf mazegen-0.1.0.tar.gz
ls mazegen-0.1.0/
# PKG-INFO  README.md  mazegen/  pyproject.toml
```

| Opción | Significado |
|---|---|
| `t` | listar el contenido |
| `x` | extraer el contenido |
| `z` | el archivo está comprimido con gzip (`.gz`) |
| `f` | a continuación va el nombre del archivo |

Qué contiene cada cosa:
- `mazegen/`: el código del generador. No incluye `ui/`, los tests ni el config, solo la parte reutilizable.
- `README.md`: la documentación del paquete (este mismo archivo).
- `pyproject.toml`: nombre, versión, dependencias y cómo se construye.
- `PKG-INFO`: los metadatos del paquete (nombre, versión, autores...), generados automáticamente.

No hace falta descomprimirlo para instalarlo; esto sirve solo para revisar qué lleva.

### Instalarlo con pip

```bash
pip install mazegen-0.1.0-py3-none-any.whl
# o, con uv:
uv pip install mazegen-0.1.0-py3-none-any.whl
```

Se puede instalar igual desde el `.tar.gz`, pero en ese caso pip tiene que construir el paquete durante la instalación (y necesita internet). El `.whl` ya viene construido, por eso es el que dejamos en el repo.

Para comprobar que funciona sin instalar nada en el proyecto:

```bash
uv run --isolated --no-project --with ./mazegen-0.1.0-py3-none-any.whl \
    python -P -c "import mazegen; print(mazegen.__file__)"
```

La ruta que sale tiene que estar en `site-packages`. El `-P` es importante: sin él, Python importaría la carpeta `mazegen/` del repo en lugar del paquete instalado.

## Funcionalidades extra

- **Colores y estilos aleatorios**: al arrancar y con la opción 3 se elige al azar entre 4 estilos de pared (grueso, fino, redondeado y doble) y 5 colores distintos para paredes, camino, "42", entrada y salida.
- **Animación del camino**: el camino más corto se va dibujando poco a poco como una línea continua. Solo se redibujan las celdas nuevas, así que no parpadea. La velocidad se ajusta con `PATH_DELAY`.
- **Recarga del config**: la opción 1 vuelve a leer `config.txt`. Si tiene un error, lo muestra unos segundos y mantiene el laberinto anterior.

## Equipo y gestión del proyecto

### Roles

<!-- TODO: revisar y completar -->
- **crblanco**: ...
- **sperez-l**: ...

### Planificación

<!-- TODO: cómo lo planteamos al principio y cómo cambió -->

### Qué funcionó bien y qué mejoraríamos

<!-- TODO -->

### Herramientas

- **Git y GitHub**, con ramas y pull requests.
- **GitHub Actions**: en cada push se pasan pytest, mypy y flake8.
- **uv** para gestionar dependencias y el entorno virtual.
- **pytest**, **mypy** (modo estricto) y **flake8**.
- **pydantic** para validar el archivo de configuración.
- **VS Code** como editor.

## Recursos

- [Maze generation algorithm – Wikipedia](https://en.wikipedia.org/wiki/Maze_generation_algorithm)
- [Maze Generation: Recursive Backtracking – Jamis Buck](https://weblog.jamisbuck.org/2010/12/27/maze-generation-recursive-backtracking)
- *Mazes for Programmers* – Jamis Buck (libro)
- [Breadth-first search – Wikipedia](https://en.wikipedia.org/wiki/Breadth-first_search)
- [ANSI escape codes – Wikipedia](https://en.wikipedia.org/wiki/ANSI_escape_code) (colores y control de la terminal)
- [Documentación de Python](https://docs.python.org/3/) y [documentación de pydantic](https://docs.pydantic.dev/)

### Uso de IA

<!-- TODO: revisar que esto refleje cómo la hemos usado de verdad -->
Hemos usado Claude Code como apoyo en:
- **Revisión y depuración**: encontrar errores (por ejemplo, un problema de rendimiento en el modo con bucles) y entender mensajes de error.
- **Tests**: actualizar y ampliar los tests cuando cambiábamos la interfaz.
- **Interfaz de terminal**: colores aleatorios, animación del camino sin parpadeo y recarga del config desde el menú.
- **Documentación**: primer borrador de este README.

Todo lo generado lo hemos revisado, probado y adaptado nosotros, y nos aseguramos de entender cada parte antes de añadirla.

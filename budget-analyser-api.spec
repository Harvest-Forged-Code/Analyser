# budget-analyser-api.spec
from PyInstaller.utils.hooks import collect_data_files, copy_metadata

# Allow importlib.metadata.version("budget-analyser") to work when frozen
datas = copy_metadata("budget-analyser")

# Bundle VERSION file so frozen builds report the correct release version
datas += [("VERSION", ".")]

# Bundle seed data (mappers + config) as read-only assets
datas += [
    ("src/budget_analyser/data/mappers", "data/mappers"),
    ("src/budget_analyser/data/config", "data/config"),
]

# uvicorn dynamic imports that PyInstaller misses
datas += collect_data_files("uvicorn")

a = Analysis(
    ["src/budget_analyser/api/main.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

# One-file mode: single executable, no extraction directory needed
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="budget-analyser-api",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    target_arch=None,
)

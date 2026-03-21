# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Threadline — single portable exe."""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = SPECPATH
WEB_BUILD = os.path.join(ROOT, 'web', 'build')

# Collect vaderSentiment lexicon data
vader_datas = collect_data_files('vaderSentiment')

# spaCy excluded from bundle — too large and causes pydantic v1 conflicts
# Regex NER still works without spaCy
spacy_datas = []
spacy_hidden = []

# sklearn if installed
sklearn_hidden = []
try:
    import sklearn
    sklearn_hidden = collect_submodules('sklearn')
except ImportError:
    pass

a = Analysis(
    [os.path.join(ROOT, 'launch.py')],
    pathex=[os.path.join(ROOT, 'src')],
    binaries=[],
    datas=[
        (WEB_BUILD, 'web/build'),  # Frontend build
        *vader_datas,
        *spacy_datas,
    ],
    hiddenimports=[
        'threadline',
        'threadline.api',
        'threadline.parser',
        'threadline.models',
        'threadline.crypto',
        'threadline.ner',
        'threadline.anomaly',
        'threadline.pairwise',
        'threadline.sentiment',
        'threadline.heatmap',
        'threadline.response_time',
        'threadline.store',
        'threadline.intel',
        'threadline.cli',
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        'fastapi',
        'starlette',
        'starlette.routing',
        'starlette.middleware',
        'starlette.middleware.cors',
        'starlette.middleware.gzip',
        'starlette.responses',
        'starlette.staticfiles',
        'anyio._backends._asyncio',
        'multipart',
        'python_multipart',
        'networkx',
        'duckdb',
        'vaderSentiment',
        'vaderSentiment.vaderSentiment',
        *spacy_hidden,
        *sklearn_hidden,
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'PIL', 'IPython', 'notebook', 'pytest', 'spacy', 'thinc', 'cymem', 'preshed', 'blis', 'srsly', 'catalogue', 'en_core_web_sm'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Threadline',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Threadline',
)

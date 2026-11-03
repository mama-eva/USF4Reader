"""Run the official SCons packaging flow and check the resulting installable archive."""

import ast
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

DEV = Path(__file__).resolve().parents[1]
(DEV / "reports").mkdir(exist_ok=True)
sys.path.insert(0, str(DEV))
from buildVars import addon_info

subprocess.run([sys.executable, "-m", "SCons", "-Q"], cwd=DEV, check=True)
version = addon_info["addon_version"]
target = DEV / "dist" / f"USF4Reader-{version}.nvda-addon"
with zipfile.ZipFile(target) as archive:
	if archive.testzip() is not None:
		raise RuntimeError("Arquivo ZIP corrompido")
	names = archive.namelist()
	required = {
		"manifest.ini",
		"appModules/ssfiv.py",
		"doc/pt_BR/readme.html",
		"doc/en/readme.html",
		"appModules/usf4reader/data/characters.json",
	}
	if not required.issubset(names):
		raise RuntimeError("Estrutura NVDA incompleta")
	if any(n.endswith((".exe", ".dll", ".pyc")) or ".." in Path(n).parts for n in names):
		raise RuntimeError("Conteúdo inesperado no complemento")
	if any(
		Path(n).suffix in (".m4s", ".emz", ".cpk", ".gfx", ".dmp")
		or Path(n).name.startswith("ui_")
		and n.endswith(".json")
		for n in names
	):
		raise RuntimeError("Recurso do jogo não pode ser redistribuído")
	for name in names:
		if name.endswith(".py"):
			ast.parse(archive.read(name).decode("utf-8"), filename=name)
	adapter = archive.read("appModules/ssfiv.py").decode("utf-8")
	if "gesture=" in adapter or "script_" in adapter or "scriptHandler" in adapter:
		raise RuntimeError("O App Module não pode registrar atalhos nesta versão")
	manifest = archive.read("manifest.ini").decode("utf-8")
	if "name = USF4Reader" not in manifest:
		raise RuntimeError("Identidade incorreta")
	if (
		f"version = {version}" not in manifest
		or 'author = "Débora Evelyn Lisboa <smartdebby29@gmail.com>"' not in manifest
	):
		raise RuntimeError("Versão ou autoria incorreta")
	if re.search(r"[A-Za-z]:[\\/]", archive.read("appModules/usf4reader/game_process.py").decode("utf-8")):
		raise RuntimeError("Caminho local não pode ser distribuído")
report = {
	"package": str(target),
	"sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
	"files": names,
	"zip_integrity": "passed",
	"python_syntax": "passed",
	"runtime_NVDA_installation": "not performed",
	"independent_executables": False,
}
(DEV / "reports" / "package-validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({k: v for k, v in report.items() if k != "files"}, indent=2))

from site_scons.site_tools.NVDATool.typings import AddonInfo

addon_info = AddonInfo(
	addon_name="USF4Reader",
	addon_summary="USF4 Reader",
	addon_description="Automatic NVDA reading of supported menus, choices, character selection and notices in Ultra Street Fighter IV.",
	addon_version="0.3.7",
	addon_changelog="Stage Select and Versus result reading, corrected round numbering, Player Data support and stability improvements. See the release notes for validation and remaining limitations.",
	addon_author="Débora Evelyn Lisboa <smartdebby29@gmail.com>",
	addon_url="https://github.com/mama-eva/USF4Reader",
	addon_sourceURL="https://github.com/mama-eva/USF4Reader",
	addon_docFileName="readme.html",
	addon_minimumNVDAVersion="2026.1.0",
	addon_lastTestedNVDAVersion="2026.1.0",
	addon_updateChannel="dev",
	addon_license="GPL-2.0-or-later",
	addon_licenseURL=None,
)
pythonSources = ["addon/appModules/*.py", "addon/appModules/usf4reader/*.py"]
i18nSources = pythonSources + ["buildVars.py"]
excludedFiles = [
	"*.pyc",
	"*.pyo",
	"**/__pycache__/*",
	"*.md",
	"**/data/ui_*.json",
	"**/data/menus.json",
]
baseLanguage = "en"
markdownExtensions = ["markdown.extensions.tables"]
brailleTables = {}
symbolDictionaries = {}
speechDictionaries = {}

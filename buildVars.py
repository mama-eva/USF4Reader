from site_scons.site_tools.NVDATool.typings import AddonInfo

addon_info = AddonInfo(
	addon_name="USF4Reader",
	addon_summary="USF4 Reader",
	addon_description="Free, open-source NVDA add-on for reading supported menus and information in Ultra Street Fighter IV.",
	addon_version="0.3.7",
	addon_changelog="Stage Select and Versus result reading, corrected round numbering, Player Data support and stability improvements. See the user guide for known limitations.",
	addon_author="Débora Evelyn Lisboa <smartdebby29@gmail.com>",
	addon_url="https://deb-evelyn.com.br/USF4Reader/",
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

"""Functional code-to-label mappings for the verified Stage Select interface."""

# Legacy text labels follow the native stage list used by VA67ff50. The six
# additional captions are images; their native names establish the code pairs.
STAGE_KEYS = {
	code: f"ID_STG_{index:04}"
	for index, code in enumerate(
		(
			"TRN",
			"CHN",
			"USA",
			"RUS",
			"BRA",
			"AFR",
			"VIE",
			"EUR",
			"RVR",
			"VCN",
			"SCO",
			"JPN",
			"LAB",
			"IND",
			"KOR",
			"BLD",
			"CNX",
			"BRX",
			"VNX",
			"JPX",
			"AFX",
			"LBX",
		)
	)
}
STAGE_KEYS.update(
	{
		"RND": "ID_STG_0024",
		"RN2": "ID_STG_0024",
		"DET": "Pitstop 109",
		"ELV": "Cosmic Elevator",
		"HFP": "Half Pipe",
		"MAD": "Mad Gear Hideout",
		"BFU": "Blast Furnace",
		"JUR": "Jurassic Era Research Facility",
	}
)

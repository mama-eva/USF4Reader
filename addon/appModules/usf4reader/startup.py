"""Verified boot-event labels and the title movie's actual input-wait state."""

LOGOS = {
	"LogoCapcom": (0x55365C, "CAPCOM"),
	"LogoNvidia": (0x5301D0, "NVIDIA"),
	"LogoDolby": (0x553794, "Dolby"),
	"LogoCRI": (0x5536FC, "CRIWARE"),
	"LogoScaleform": (0x553804, "Scaleform"),
}


def title_ready(scaleform, event):
	wrapper = scaleform.memory.u32(event + 0x44)
	if not wrapper:
		return False
	sprite, root = scaleform.movie_root(scaleform.memory.u32(wrapper))
	if not root or not scaleform.visible(sprite):
		return False
	# Frame-one script sets MSG_WAIT; SendDecide changes it to MSG_DECIDED.
	# Do not follow the blinking press_start clip visibility: that would repeat speech.
	return scaleform.field(root, "state_") == "MSG_WAIT"

"""Strict parsers for formats identified in the supplied game files."""

import struct
import zlib


class FormatError(ValueError):
	pass


def parse_m4s(data):
	"""#M4S: 0x20 header, 8-byte entries, two offsets relative to each entry."""
	if len(data) < 32 or data[:4] != b"#M4S" or data[8:10] != b"\xfe\xff":
		raise FormatError("Cabeçalho M4S não reconhecido")
	count, table = struct.unpack_from("<II", data, 16)
	if table < 32 or count > 100000 or table + count * 8 > len(data):
		raise FormatError("Tabela M4S fora do arquivo")
	strings_start = table + count * 8
	entries = {}
	for i in range(count):
		pos = table + i * 8
		key_offset, text_offset = struct.unpack_from("<II", data, pos)
		key_offset += pos
		text_offset += pos
		if not strings_start <= key_offset < len(data) or not strings_start <= text_offset < len(data):
			raise FormatError("Offset M4S inválido")
		key_end = data.find(b"\0", key_offset)
		if key_end < 0 or text_offset % 2:
			raise FormatError("String M4S inválida")
		text_end = text_offset
		while text_end + 1 < len(data) and data[text_end : text_end + 2] != b"\0\0":
			text_end += 2
		if text_end + 1 >= len(data):
			raise FormatError("Texto UTF-16 sem terminador")
		try:
			key = data[key_offset:key_end].decode("ascii")
			text = data[text_offset:text_end].decode("utf-16-le")
		except UnicodeError as error:
			raise FormatError("Codificação M4S inválida") from error
		if key in entries and entries[key] != text:
			raise FormatError("Chave M4S repetida com textos distintos")
		entries[key] = text
	return data[4:8].decode("ascii").lstrip("#"), entries


def unpack_emz(data, limit=64 * 1024 * 1024):
	"""#EMZ wrapper followed by raw DEFLATE, not a zlib-wrapped stream."""
	if len(data) < 16 or data[:4] != b"#EMZ":
		raise FormatError("Cabeçalho EMZ não reconhecido")
	expected, offset = struct.unpack_from("<II", data, 8)
	if not 0 < expected <= limit or offset != 16:
		raise FormatError("Tamanho ou offset EMZ não suportado")
	decoder = zlib.decompressobj(-15)
	try:
		result = decoder.decompress(data[offset:], expected + 1)
	except zlib.error as error:
		raise FormatError("DEFLATE EMZ inválido") from error
	if len(result) != expected or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
		raise FormatError("Comprimento EMZ inconsistente")
	return result

# © 2020 io mintz <io@mintz.cc>

import re
from http import HTTPStatus
from typing import ClassVar, List, TYPE_CHECKING

from .designs.format import PALETTE_SIZE, MAX_DESIGN_TILES, MAX_NAME_LEN, BYTES_PER_PIXEL, WIDTH, HEIGHT

if TYPE_CHECKING:
	from .designs.encode import Layer

class ACNHError(Exception):
	code: ClassVar[int]
	message: ClassVar[str]
	http_status: ClassVar[int]

	def __int__(self):
		return self.code

	def to_dict(self):
		return {'error': self.message.format(self), 'error_code': self.code, 'http_status': self.http_status}

class InvalidFormatError(ACNHError):
	http_status = HTTPStatus.BAD_REQUEST
	regex: re.Pattern

	def to_dict(self):
		d = super().to_dict()
		d['validation_regex'] = self.regex.pattern
		return d

	@classmethod
	def validate(cls, s):
		if not cls.regex.fullmatch(s):
			raise cls
		return s

class DodoCodeError(ACNHError):
	pass

class UnknownDodoCodeError(DodoCodeError):
	code = 101
	http_status = HTTPStatus.NOT_FOUND
	message = 'unknown dodo code'

class InvalidDodoCodeError(DodoCodeError, InvalidFormatError):
	code = 102
	message = 'invalid dodo code'
	regex = re.compile(r'[A-HJ-NP-Y0-9]{5}')

class ImageError(ACNHError):
	pass

class DesignError(ACNHError):
	pass

class UnknownDesignCodeError(DesignError):
	code = 201
	message = 'unknown design code'
	http_status = HTTPStatus.NOT_FOUND

class InvalidDesignCodeError(DesignError, InvalidFormatError):
	code = 202
	message = 'invalid design code'

	DESIGN_CODE_ALPHABET = '0123456789BCDFGHJKLMNPQRSTVWXY'
	DESIGN_CODE_ALPHABET_VALUES = {c: val for val, c in enumerate(DESIGN_CODE_ALPHABET)}

	_design_code_segment = f'[{DESIGN_CODE_ALPHABET}]{{4}}'
	regex = re.compile('-'.join([_design_code_segment] * 3))
	del _design_code_segment

class UnknownAuthorIdError(DesignError):
	code = 203
	message = 'unknown author ID'
	http_status = HTTPStatus.NOT_FOUND

class InvalidAuthorIdError(DesignError, InvalidFormatError):
	code = 204
	message = 'invalid author ID'
	regex = re.compile(r'\d{4}-?\d{4}-?\d{4}', re.ASCII)

class InvalidScaleFactorError(InvalidFormatError):
	message = 'invalid scale factor'
	code = 205
	regex = re.compile(r'[123456]')

class InvalidLayerIndexError(DesignError):
	code = 206
	message = 'Invalid layer index'

	def __init__(self, *, num_layers):
		super().__init__()
		self.num_layers = num_layers

	def to_dict(self):
		d = super().to_dict()
		d['num_layers'] = self.num_layers

class InvalidLayerNameError(DesignError):
	code = 207
	message = 'Invalid layer name'
	valid_layer_names: List[str]
	http_status = HTTPStatus.BAD_REQUEST

	def __init__(self, design):
		super().__init__()
		self.valid_layer_names = list(design.external_layer_names)

	def to_dict(self):
		d = super().to_dict()
		d['valid_layer_names'] = self.valid_layer_names
		return d

class InvalidProArgument(DesignError, InvalidFormatError):
	message = 'invalid value for pro argument'
	code = 208
	regex = re.compile(r'[01]|(?:false|true)|[ft]', re.IGNORECASE)

class CannotScaleThumbnailError(DesignError):
	message = 'cannot scale thumbnails'
	code = 209
	http_status = HTTPStatus.BAD_REQUEST

# not an invalid format error because it's not constrainable to a regex
class InvalidDesignError(DesignError):
	code = 210
	message = 'Nintendo did not like your design for some reason. (Invalid name, perhaps?)'
	http_status = HTTPStatus.BAD_REQUEST

class InvalidPaletteError(DesignError):
	code = 211
	message = f'the combined palette of all layers exceeds {PALETTE_SIZE} colors'
	http_status = HTTPStatus.BAD_REQUEST

class DesignLitTheServerOnFireError(InvalidDesignError, DesignError):
	code = 212

class UnknownImageIdError(ImageError):
	code = 301
	message = 'unknown image ID'
	http_status = HTTPStatus.NOT_FOUND

class InvalidImageIdError(ImageError, InvalidFormatError):
	code = 302
	message = 'Invalid image ID.'
	regex = re.compile(r'[0-9]+')

class DeletionDeniedError(ImageError):
	code = 303
	message = 'you do not own this image'
	http_status = HTTPStatus.UNAUTHORIZED

class InvalidLayerSizeError(ImageError):
	code = 305
	message = 'layer {0.name} was not {0.width}×{0.height}.'
	http_status = HTTPStatus.BAD_REQUEST

	def __init__(self, name, width, height):
		super().__init__()
		self.name = name
		self.width = width
		self.height = height

	def to_dict(self):
		d = super().to_dict()
		d['expected_width'] = self.width
		d['expected_height'] = self.height
		d['expected_byte_length'] = self.width * self.height * BYTES_PER_PIXEL
		return d

def num_tiles(width, height):
	return width // WIDTH * height // HEIGHT

class TiledImageTooBigError(ImageError):
	code = 306
	message = (
		f'The uploaded image would create {{.num_tiles}} tiles, which is greater than the limit, {MAX_DESIGN_TILES}.'
	)
	http_status = HTTPStatus.REQUEST_ENTITY_TOO_LARGE

	def __init__(self, img):
		super().__init__()
		self.num_tiles = num_tiles(*img.size)

	@classmethod
	def validate(cls, img):
		ex = cls(img)
		if ex.num_tiles > MAX_DESIGN_TILES:
			raise ex

class InvalidImageArgument(ImageError):
	code = 307
	message = 'missing or invalid required image argument {.argument_name}'
	http_status = HTTPStatus.BAD_REQUEST

	def __init__(self, argument_name):
		super().__init__()
		self.argument_name = argument_name

	def to_dict(self):
		d = super().to_dict()
		d['argument_name'] = self.argument_name
		return d

class InvalidLayerError(DesignError):
	layer: 'Layer'
	http_status = HTTPStatus.BAD_REQUEST

	def __init__(self, layer):
		super().__init__()
		self.layer = layer

	def to_dict(self):
		d = super().to_dict()
		d['layer_name'] = self.layer.name
		d['layer_size'] = self.layer.size
		return d

class MissingLayerError(InvalidLayerError):
	code = 309
	message = 'Payload was missing one or more layers. First missing layer: "{0.layer.name}"'
	http_status = HTTPStatus.BAD_REQUEST

class InvalidImageError(ImageError):
	code = 310
	message = 'One or more layers submitted represented an invalid image.'
	http_status = HTTPStatus.BAD_REQUEST

class ImageNameTooLongError(ImageError):
	code = 312
	message = 'The name provided was too long. Maximum in this case is {.max_len} characters.'
	http_status = HTTPStatus.BAD_REQUEST

	def __init__(self, max_len):
		super().__init__()
		self.max_len = max_len

	@classmethod
	def validate(cls, design):
		img = design.layer_images['0']
		overhead = len(f' {num_tiles(*img.size)}')
		if design.design_name is not None and len(design.design_name) + overhead > MAX_NAME_LEN:
			self = cls(MAX_NAME_LEN - overhead)
			raise self
		return design

	def to_dict(self):
		d = super().to_dict()
		d['max_length'] = self.max_len
		return d

class InvalidPaginationError(ACNHError):
	http_status = HTTPStatus.BAD_REQUEST

class TwoPaginationReferencesPassedError(ACNHError):
	code = 401
	message = 'Only one of "before" or "after" may be specified.'

class InvalidPaginationLimitError(InvalidFormatError, InvalidPaginationError):
	code = 402
	message = 'Invalid limit passed'
	regex = re.compile('[0-9]+')

class AuthorizationError(ACNHError):
	pass

class MissingUserAgentStringError(AuthorizationError):
	code = 901
	message = 'User-Agent header required'
	http_status = HTTPStatus.BAD_REQUEST

class IncorrectAuthorizationError(AuthorizationError):
	code = 902
	message = 'invalid or incorrect Authorization header'
	http_status = HTTPStatus.UNAUTHORIZED

	def __init__(self, path=None):
		self.path = path
		super().__init__()

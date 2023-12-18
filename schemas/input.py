INPUT_SCHEMA = {
    'source_image': {
        'type': str,
        'required': True
    },
    'model': {
        'type': str,
        'required': False,
        'default': 'RealESRGAN_x4plus',
        'constraints': lambda model: model in [
            'RealESRGAN_x4plus',
            'RealESRNet_x4plus',
            'RealESRGAN_x4plus_anime_6B',
            'RealESRGAN_x2plus',
        ]
    },
    'scale': {
        'type': float,
        'required': False,
        'default': 2,
        'constraints': lambda scale: 0 < scale < 16
    },
    'face_enhance': {
        'type': bool,
        'required': False,
        'default': False
    },
    'tile': {
        'type': int,
        'required': False,
        'default': 0,
    },
    'tile_pad': {
        'type': int,
        'required': False,
        'default': 10,
    },
    'pre_pad': {
        'type': int,
        'required': False,
        'default': 0,
    },
    'half': {
        'type': bool,
        'required': False,
        'default': False
    },
    'filter_speckle': {
        'type': int,
        'required': False,
        'default': 4,
    },
    'color_precision': {
        'type': int,
        'required': False,
        'default': 6,
    },
    'layer_difference': {
        'type': int,
        'required': False,
        'default': 16,
    },
    'corner_threshold': {
        'type': int,
        'required': False,
        'default': 60,
    },
    'length_threshold': {
        'type': float,
        'required': False,
        'default': 4.0,
    },
    'max_iterations': {
        'type': int,
        'required': False,
        'default': 10,
    },
    'splice_threshold': {
        'type': int,
        'required': False,
        'default': 45,
    },
    'path_precision': {
        'type': int,
        'required': False,
        'default': 3,
    },

}

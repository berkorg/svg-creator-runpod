import os
import io
import uuid
import base64
import cv2
import glob
import traceback
import runpod
from runpod.serverless.utils.rp_validator import validate
from runpod.serverless.modules.rp_logger import RunPodLogger
from basicsr.archs.rrdbnet_arch import RRDBNet
from basicsr.utils.download_util import load_file_from_url
from realesrgan import RealESRGANer

# from realesrgan.archs.srvgg_arch import SRVGGNetCompac
from PIL import Image
from schemas.input import INPUT_SCHEMA
import vtracer

GPU_ID = 0
VOLUME_PATH = "/workspace"
TMP_PATH = f"{VOLUME_PATH}/tmp"
MODELS_PATH = f"{VOLUME_PATH}/models/ESRGAN"
GFPGAN_MODEL_PATH = f"{VOLUME_PATH}/models/GFPGAN/GFPGANv1.3.pth"
logger = RunPodLogger()


# ---------------------------------------------------------------------------- #
# Application Functions                                                        #
# ---------------------------------------------------------------------------- #
def upscale(
    source_image_path,
    image_extension,
    model_name="RealESRGAN_x4plus_anime_6B",
    outscale=2,
    face_enhance=False,
    tile=0,
    tile_pad=10,
    pre_pad=0,
    half=False,
    denoise_strength=0.5,
    filter_speckle=4,
    color_precision=6,
    layer_difference=16,
    corner_threshold=60,
    length_threshold=4.0,
    max_iterations=10,
    splice_threshold=45,
    path_precision=3,
):
    """
    model_name options:
        - RealESRGAN_x4plus
        - RealESRNet_x4plus
        - RealESRGAN_x4plus_anime_6B
        - RealESRGAN_x2plus
        - realesr-animevideov3
        - realesr-general-x4v3

    image_extension: .jpg or .png

    outscale: The final upsampling scale of the image

    face_enhance: Whether or not to enhance the face

    tile: Tile size, 0 for no tile during testing

    tile_pad: Tile padding (default = 10)

    pre_pad: Pre padding size at each border

    denoise_strength: 0 for weak denoise (keep noise)
                      1 for strong denoise ability
                      Only used for the realesr-general-x4v3 model
    """

    # determine models according to model names
    model_name = model_name.split(".")[0]

    if image_extension == ".jpg":
        image_format = "JPEG"
    elif image_extension == ".png":
        image_format = "PNG"
    else:
        raise ValueError(f"Unsupported image type, must be either JPEG or PNG")

    if model_name == "RealESRGAN_x4plus":  # x4 RRDBNet model
        model = RRDBNet(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_block=23,
            num_grow_ch=32,
            scale=4,
        )
        netscale = 4
    elif model_name == "RealESRNet_x4plus":  # x4 RRDBNet model
        model = RRDBNet(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_block=23,
            num_grow_ch=32,
            scale=4,
        )
        netscale = 4
    elif model_name == "RealESRGAN_x4plus_anime_6B":  # x4 RRDBNet model with 6 blocks
        model = RRDBNet(
            num_in_ch=3, num_out_ch=3, num_feat=64, num_block=6, num_grow_ch=32, scale=4
        )
        netscale = 4
    elif model_name == "RealESRGAN_x2plus":  # x2 RRDBNet model
        model = RRDBNet(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_block=23,
            num_grow_ch=32,
            scale=2,
        )
        netscale = 2
    # TODO: Implement these
    # elif model_name == 'realesr-animevideov3':  # x4 VGG-style model (XS size)
    #     model = SRVGGNetCompact(num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=16, upscale=4, act_type='prelu')
    #     netscale = 4
    #     file_url = ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-animevideov3.pth']
    # elif model_name == 'realesr-general-x4v3':  # x4 VGG-style model (S size)
    #     model = SRVGGNetCompact(num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=32, upscale=4, act_type='prelu')
    #     netscale = 4
    #     file_url = [
    #         'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-wdn-x4v3.pth',
    #         'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth'
    #     ]
    elif model_name == "4x-UltraSharp":  # x4 RRDBNet model
        model = RRDBNet(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_block=23,
            num_grow_ch=32,
            scale=4,
        )
        netscale = 4
    elif model_name == "lollypop":  # x4 RRDBNet model
        model = RRDBNet(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_block=23,
            num_grow_ch=32,
            scale=4,
        )
        netscale = 4
    else:
        raise ValueError(f"Unsupported model: {model_name}")

    # determine model paths
    model_path = os.path.join(MODELS_PATH, model_name + ".pth")

    if not os.path.isfile(model_path):
        raise Exception(f"Could not find model: {model_path}")

    # use dni to control the denoise strength
    dni_weight = None
    # if model_name == 'realesr-general-x4v3' and denoise_strength != 1:
    #     wdn_model_path = model_path.replace('realesr-general-x4v3', 'realesr-general-wdn-x4v3')
    #     model_path = [model_path, wdn_model_path]
    #     dni_weight = [denoise_strength, 1 - denoise_strength]

    upsampler = RealESRGANer(
        scale=netscale,
        model_path=model_path,
        dni_weight=dni_weight,
        model=model,
        tile=tile,
        tile_pad=tile_pad,
        pre_pad=pre_pad,
        half=half,
        gpu_id=GPU_ID,
    )

    img = cv2.imread(source_image_path, cv2.IMREAD_UNCHANGED)
    img = cv2.resize(img, (256, 256))

    if img is None:
        raise RuntimeError(f"Source image ({source_image_path}) is corrupt")

    try:
        output, _ = upsampler.enhance(img, outscale=outscale)
    except RuntimeError as e:
        raise RuntimeError(e)
    else:
        result_image = Image.fromarray(cv2.cvtColor(output, cv2.COLOR_BGR2RGB))

        upscaled_image_path = f"{TMP_PATH}/upscaled_{uuid.uuid4()}.png"
        result_image.save(upscaled_image_path)

        svg_save_path = f"{TMP_PATH}/upscaled_{uuid.uuid4()}.svg"
        convert_to_svg(
            upscaled_image_path,
            svg_save_path,
            filter_speckle,
            color_precision,
            layer_difference,
            corner_threshold,
            length_threshold,
            max_iterations,
            splice_threshold,
            path_precision,
        )

        with open(svg_save_path, "r") as svg_file:
            svg_data = svg_file.read()

        # Clean up temporary images
        os.remove(upscaled_image_path)
        os.remove(svg_save_path)
        return svg_data


def convert_to_svg(
    image_path,
    output_path,
    filter_speckle=4,  # default: 4
    color_precision=6,  # default: 6
    layer_difference=16,  # default: 16
    corner_threshold=60,  # default: 60
    length_threshold=4.0,  # in [3.5, 10] default: 4.0
    max_iterations=10,  # default: 10
    splice_threshold=45,  # default: 45
    path_precision=3,  # default: 8):
):
    try:
        vtracer.convert_image_to_svg_py(
            image_path,
            output_path,
            filter_speckle,
            color_precision,
            layer_difference,
            corner_threshold,
            length_threshold,
            max_iterations,
            splice_threshold,
            path_precision,
        )
    except Exception as e:
        logger.error(f"An exception was raised: {e}")

        return {"error": traceback.format_exc(), "refresh_worker": True}


def determine_file_extension(image_data):
    image_extension = None

    try:
        if image_data.startswith("/9j/"):
            image_extension = ".jpg"
        elif image_data.startswith("iVBORw0Kg"):
            image_extension = ".png"
        else:
            # Default to png if we can't figure out the extension
            image_extension = ".png"
    except Exception as e:
        image_extension = ".png"

    return image_extension


def upscaling_api(input):
    if not os.path.exists(TMP_PATH):
        os.makedirs(TMP_PATH)

    unique_id = uuid.uuid4()
    source_image_data = input["source_image"]
    model_name = input["model"]
    outscale = input["scale"]
    face_enhance = input["face_enhance"]
    tile = input["tile"]
    tile_pad = input["tile_pad"]
    pre_pad = input["pre_pad"]
    half = input["half"]
    filter_speckle = input["filter_speckle"]
    color_precision = input["color_precision"]
    layer_difference = input["layer_difference"]
    corner_threshold = input["corner_threshold"]
    length_threshold = input["length_threshold"]
    max_iterations = input["max_iterations"]
    splice_threshold = input["splice_threshold"]
    path_precision = input["path_precision"]

    # Decode the source image data
    source_image = base64.b64decode(source_image_data)
    source_file_extension = determine_file_extension(source_image_data)
    source_image_path = f"{TMP_PATH}/source_{unique_id}{source_file_extension}"

    # Save the source image to disk
    with open(source_image_path, "wb") as source_file:
        source_file.write(source_image)

    try:
        result_svg_string = upscale(
            source_image_path,
            source_file_extension,
            model_name,
            outscale,
            face_enhance,
            tile,
            tile_pad,
            pre_pad,
            half,
            filter_speckle,
            color_precision,
            layer_difference,
            corner_threshold,
            length_threshold,
            max_iterations,
            splice_threshold,
            path_precision,
        )
    except Exception as e:
        logger.error(f"An exception was raised: {e}")

        return {"error": traceback.format_exc(), "refresh_worker": True}

    # Clean up temporary images
    os.remove(source_image_path)

    return {"svg": result_svg_string}


# ---------------------------------------------------------------------------- #
# RunPod Handler                                                               #
# ---------------------------------------------------------------------------- #
def handler(event):
    validated_input = validate(event["input"], INPUT_SCHEMA)

    if "errors" in validated_input:
        return {"errors": validated_input["errors"]}

    return upscaling_api(validated_input["validated_input"])


if __name__ == "__main__":
    logger.info("Starting RunPod Serverless...")
    runpod.serverless.start({"handler": handler})

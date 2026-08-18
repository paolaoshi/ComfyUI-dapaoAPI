"""Shared preprocessing for user supplied ComfyUI IMAGE inputs.

The relay should not receive 4K/8K source images by accident.  Keep the
longest edge at or below 2K while using a high quality Lanczos resize and
lossless PNG encoding for references.
"""

import base64
import io

import numpy as np
from PIL import Image


MAX_INPUT_IMAGE_EDGE = 2048


def resize_pil_for_input(image: Image.Image, max_edge: int = MAX_INPUT_IMAGE_EDGE) -> Image.Image:
    """Return an image whose longest edge is no larger than ``max_edge``."""
    image = image.copy()
    limit = max(1, min(int(max_edge or MAX_INPUT_IMAGE_EDGE), MAX_INPUT_IMAGE_EDGE))
    largest = max(image.size)
    if largest <= limit:
        return image
    scale = limit / float(largest)
    size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
    return image.resize(size, Image.Resampling.LANCZOS)


def tensor_to_pil_images(image_tensor, max_edge: int = MAX_INPUT_IMAGE_EDGE) -> list[Image.Image]:
    """Convert a ComfyUI IMAGE batch to resized PIL images."""
    if image_tensor is None or not hasattr(image_tensor, "shape") or len(image_tensor.shape) != 4:
        raise ValueError("图片输入必须是 ComfyUI IMAGE 批次。")
    result = []
    for index in range(int(image_tensor.shape[0])):
        array = np.clip(image_tensor[index].detach().cpu().numpy() * 255.0, 0, 255).astype(np.uint8)
        if array.ndim != 3 or array.shape[2] < 3:
            raise ValueError("图片输入必须是 RGB 或 RGBA IMAGE。")
        mode = "RGBA" if array.shape[2] >= 4 else "RGB"
        result.append(resize_pil_for_input(Image.fromarray(array[:, :, :4] if mode == "RGBA" else array[:, :, :3], mode=mode), max_edge))
    return result


def tensor_to_png_bytes(image_tensor, max_edge: int = MAX_INPUT_IMAGE_EDGE) -> list[bytes]:
    result = []
    for image in tensor_to_pil_images(image_tensor, max_edge):
        buffer = io.BytesIO()
        image.save(buffer, format="PNG", optimize=True)
        result.append(buffer.getvalue())
    return result


def tensor_to_png_data_uris(image_tensor, max_edge: int = MAX_INPUT_IMAGE_EDGE) -> list[str]:
    return ["data:image/png;base64," + base64.b64encode(value).decode("ascii") for value in tensor_to_png_bytes(image_tensor, max_edge)]


def tensor_to_png_inline_parts(image_tensor, max_edge: int = MAX_INPUT_IMAGE_EDGE) -> list[dict]:
    return [
        {"inlineData": {"mimeType": "image/png", "data": base64.b64encode(value).decode("ascii")}}
        for value in tensor_to_png_bytes(image_tensor, max_edge)
    ]


IMAGE_429_HINT = (
    "请求被限流或排队，请稍后重试。若本次上传了图片，请先检查每张图片的最长边是否超过2048像素（2K）；"
    "多张参考图也必须逐张控制在2K以内，过大的8K/4K图片可能触发上游排队。"
)


__all__ = [
    "MAX_INPUT_IMAGE_EDGE",
    "resize_pil_for_input",
    "tensor_to_pil_images",
    "tensor_to_png_bytes",
    "tensor_to_png_data_uris",
    "tensor_to_png_inline_parts",
    "IMAGE_429_HINT",
]

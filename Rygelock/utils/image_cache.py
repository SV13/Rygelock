# utils/image_cache.py
from typing import Dict
from PIL import Image
import customtkinter as ctk
from .resource_path import resource_path

class ImageCache:
    _pil: Dict[str, Image.Image] = {}
    _ctk: Dict[str, ctk.CTkImage] = {}

    @classmethod
    def pil(cls, rel_path: str) -> Image.Image:
        if rel_path not in cls._pil:
            cls._pil[rel_path] = Image.open(resource_path(rel_path))
        return cls._pil[rel_path]

    @classmethod
    def ctk(cls, rel_path: str, size=None) -> ctk.CTkImage:
        key = f"{rel_path}|{size}"
        if key not in cls._ctk:
            img = cls.pil(rel_path)
            cls._ctk[key] = ctk.CTkImage(light_image=img if size is None else img.resize(size))
        return cls._ctk[key]

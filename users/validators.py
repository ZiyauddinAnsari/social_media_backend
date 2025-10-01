from django.conf import settings
from django.core.exceptions import ValidationError
from PIL import Image
from io import BytesIO


def validate_media_file(uploaded_file):
    """Validate uploaded file against size and allowed content types.
    Returns a metadata dict (content_type, size, width, height) for images.
    Raises ValidationError on failure.
    """
    max_size = getattr(settings, 'MEDIA_MAX_SIZE', 5 * 1024 * 1024)
    allowed = set(getattr(settings, 'MEDIA_ALLOWED_CONTENT_TYPES', []))

    size = getattr(uploaded_file, 'size', 0)
    ctype = getattr(uploaded_file, 'content_type', None) or ''

    if size == 0:
        raise ValidationError('Empty file upload is not allowed')
    if size > max_size:
        raise ValidationError(f'File exceeds maximum size of {max_size} bytes')
    if allowed and ctype not in allowed:
        raise ValidationError(f'Unsupported content type: {ctype}')

    width = height = None
    if ctype.startswith('image/'):
        try:
            # Pillow can handle file-like; ensure pointer at start
            pos = uploaded_file.tell() if hasattr(uploaded_file, 'tell') else None
            if hasattr(uploaded_file, 'seek'):
                uploaded_file.seek(0)
            img = Image.open(uploaded_file)
            width, height = img.size
            img.verify()  # Validate image integrity
            if hasattr(uploaded_file, 'seek') and pos is not None:
                uploaded_file.seek(pos)
        except Exception:
            raise ValidationError('Invalid image file')

    return {
        'content_type': ctype,
        'size': size,
        'width': width,
        'height': height,
    }

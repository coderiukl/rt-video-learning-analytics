import os

import cloudinary.uploader
from cloudinary_storage.storage import UploadedFile, VideoMediaCloudinaryStorage
from django.conf import settings


class LargeVideoCloudinaryStorage(VideoMediaCloudinaryStorage):
    def _upload(self, name, content):
        options = {
            "use_filename": True,
            "resource_type": self._get_resource_type(name),
            "tags": self.TAG,
            "chunk_size": getattr(settings, "CLOUDINARY_VIDEO_CHUNK_SIZE", 20 * 1024 * 1024),
        }
        folder = os.path.dirname(name)
        if folder:
            options["folder"] = folder
        return cloudinary.uploader.upload_large(content, **options)

    def _save(self, name, content):
        name = self._normalise_name(name)
        name = self._prepend_prefix(name)
        content = UploadedFile(content, name)
        response = self._upload(name, content)
        return response["public_id"]

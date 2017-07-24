__version__ = '1.0'

import os
from itertools import ifilter

from PIL import Image

from django.db import models
from django.db.transaction import atomic


class CleanupFileModel(models.Model):
    class Meta:
        abstract = True

    def _get_file_fields(self):
        for field, _ in type(self)._meta.get_fields():
            if issubclass(type(field), models.FileField):
                yield field

    def delete(self, *args, **kwargs):
        for field in self._get_file_fields():
            try:
                getattr(self, field.name).delete()
            except Exception:
                pass

        super(CleanupFileModel, self).delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        files_to_delete = {}

        if self.id:
            db_instance = type(self).objects.get(id=self.id)

            for field in self._get_file_fields():
                val = getattr(db_instance, field.name, None)
                if val:
                    files_to_delete[field.name] = getattr(val, 'path', None)

        super(CleanupFileModel, self).save(*args, **kwargs)

        for field_name in files_to_delete:
            val = getattr(self, field_name, None)

            if field_name in files_to_delete and ((files_to_delete[field_name] and not val)
                                                  or files_to_delete[field_name] != getattr(val, 'path', None)):
                try:
                    os.remove(files_to_delete[field_name])
                except Exception:
                    pass


class CropImageModel(CleanupFileModel):
    class Meta:
        abstract = True

    def _get_crop_fields(self):
        for field in self._meta.fields:
            if isinstance(field, models.ImageField) and getattr(self, field.name + '_width', None) and \
                        getattr(self, field.name + '_height', None):
                yield field

    def save(self, *args, **kwargs):
        update_map = {}

        with atomic():
            for field in self._get_crop_fields():
                update_picture = not self.id

                if self.id:
                    db_instance = type(self).objects.get(id=self.id)
                    update_picture = getattr(db_instance, field.name) != getattr(self, field.name)

                update_map[field] = update_picture and getattr(self, field.name)

            super(CropImageModel, self).save(*args, **kwargs)

            for field in self._get_crop_fields():
                if update_map[field]:
                    self.crop_image(
                        Image.open(getattr(self, field.name).path).convert("RGBA"),
                        getattr(self, field.name + '_width'),
                        getattr(self, field.name + '_height')
                    ).save(getattr(self, field.name).path, quality=100)

    @staticmethod
    def crop_image(im, max_width, max_height):
        width, height = im.size
        k = max(float(max_width) / width, float(max_height) / height)
        width, height = width * k, height * k

        im = im.resize((int(width), int(height)), Image.ANTIALIAS)

        x0, y0 = map(int, ((width - max_width) / 2,
                           (height - max_height) / 2))

        return im.crop((x0, y0, x0 + max_width, y0 + max_height))


class ThumbPictureModel(CleanupFileModel):
    class Meta:
        abstract = True

    @classmethod
    def resize_picture(cls, image_path, width, height, max_width, max_height):
        if (max_width and width > max_width) or (max_height and height > max_height):
            img = Image.open(image_path).convert("RGBA")
            img.thumbnail((max_width if max_width else width, max_height if max_height else height), Image.ANTIALIAS)
            img.save(image_path, quality=100)

    def _get_images_fields(self):
        return ifilter(lambda val: isinstance(val, models.ImageField), self._meta.fields)

    def save(self, *args, **kwargs):
        pictures_fields = {}

        for field in self._get_images_fields():
            max_width = getattr(self, field.name + '_max_width', None)
            max_height = getattr(self, field.name + '_max_height', None)

            if max_width or max_height:
                pictures_fields[field.name] = (max_width, max_height)

        db_instance = None

        if self.pk:
            try:
                db_instance = type(self).objects.get(pk=self.pk)
            except self.DoesNotExist:
                pass

        super(ThumbPictureModel, self).save(*args, **kwargs)

        for field_name, image_sizes in pictures_fields.items():
            db_field_value = getattr(db_instance, field_name, None)
            field_value = getattr(self, field_name, None)

            if db_instance and db_field_value and db_field_value != field_value:
                db_field_value.delete(False)

            if field_value and os.path.exists(field_value.path):
                self.resize_picture(field_value.path, field_value.width, field_value.height, *image_sizes)

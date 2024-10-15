import os
import glob
import pytz
import re

import json
import torch

# Celery
from celery import shared_task
# Celery-progress
from celery_progress.backend import ProgressRecorder

from django.conf import settings
from django.utils.dateparse import parse_datetime

from torch.utils.data import DataLoader
from facenet_pytorch import MTCNN

from photo.facedetectlib import ImageFolderCustom
from photo.models import Album, Photo

from photo.models import Album, Photo, Tag, PhotoTag
from photo.lib import get_exif, add_tags


def collate_fn(x):
    return x[0]

@shared_task(bind=True)
def FaceDetection(self, album_id):

    print("Task started")
    progress_recorder = ProgressRecorder(self)
    album = Album.objects.get(id=album_id)

    input_path = os.path.join(settings.PHOTO_ROOT, album.name[1:])

    workers = 0 if os.name == 'nt' else 4
    dataset = ImageFolderCustom(input_path)
    loader = DataLoader(dataset, collate_fn=collate_fn, num_workers=workers)
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    mtcnn = MTCNN(
        image_size=3600, margin=0, min_face_size=150,
        thresholds=[0.7, 0.8, 0.8], factor=0.709, post_process=True,
        device=device, keep_all=True
    )
    for idx, (x, y) in enumerate(loader):
        item, id = dataset.__getitem__(idx)
        filename = os.path.basename(item.filename)
        photo = Photo.objects.get(file=filename)

        x_aligned = mtcnn(x)
        boxes, probs, points = mtcnn.detect(x, landmarks=True)

        save_boxes = []
        if x_aligned is not None:
            for i, (box, prob, point) in enumerate(zip(boxes, probs, points)):
                if prob > 0.90:
                    save_boxes.append(box.tolist())

        json_str = json.dumps(save_boxes)
        if len(save_boxes) > 0:
            photo.set_prop('face_annotate', json_str)
            photo.set_prop('face_count', len(save_boxes))

        progress_recorder.set_progress(idx, len(loader), description="Detecting faces")

    print("ended")
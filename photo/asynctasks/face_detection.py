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

from torch.utils.data import DataLoader
from torchvision import transforms
from facenet_pytorch import MTCNN
from PIL import Image

from photo.facedetectlib import ImageFolderCustom


from photo.models import Album, Photo


def collate_fn(batch):
    images = []
    targets = []
    paths = []

    for img, target, path in batch:
        images.append(img)
        targets.append(target)
        paths.append(path)

    images = torch.stack(images)
    targets = torch.tensor(targets)

    return images, targets, paths


@shared_task(bind=True)
def FaceDetection(self, album_id):
    print("Task started")
    progress_recorder = ProgressRecorder(self)
    album = Album.objects.get(id=album_id)

    input_path = os.path.join(settings.PHOTO_ROOT, album.name[1:])

    workers = 0 if os.name == 'nt' else 4
    transform = transforms.ToTensor()
    print(input_path)
    dataset = ImageFolderCustom(input_path, transform=transform)

    print("dataset created")

    loader = DataLoader(dataset,  collate_fn=collate_fn, num_workers=workers)

    print(" data loader created")
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    mtcnn = MTCNN(
        image_size=None , margin=0, min_face_size=150,
        thresholds=[0.7, 0.8, 0.8], factor=0.709, post_process=True,
        device=device, keep_all=True
    )

    for idx, data in enumerate(loader):
        x, y, paths = data
        path = paths[0]
        print(path)
        filename = os.path.basename(path)
        print(f"idx {idx}")
        print(f"filename {filename}")
        try:
            photo = Photo.objects.get(file=filename)
            print(f"processing {photo}")
            print(x.shape)
            print(x)
            print(type(x))
            x_aligned = mtcnn(x)  # pass in the single image from the batch.

            if x_aligned is not None: # only run detect if x_aligned is not none.
                boxes, probs, points = mtcnn.detect(x, landmarks=True)

                save_boxes = []
                for box, prob, point in zip(boxes, probs, points):
                    if prob > 0.90:
                        save_boxes.append(box.tolist())

                json_str = json.dumps(save_boxes)
                if len(save_boxes) > 0:
                    photo.set_prop('face_annotate', json_str)
                    photo.set_prop('face_count', len(save_boxes))
                print(f"saved {photo}")

            else:
                print(f"No faces detected in {filename}")

            progress_recorder.set_progress(idx, len(loader), description="Detecting faces")
        except RuntimeError as e:
            print(f"Error processing {filename}: {e}")
            continue
        except Photo.DoesNotExist:
            print(f"Photo with filename {filename} does not exist in the database.")
            continue

        progress_recorder.set_progress(idx, len(loader), description="Detecting faces")

    print("ended")
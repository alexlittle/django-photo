import os
import json
import torch

from django.conf import settings
from django.core.management.base import BaseCommand


from torch.utils.data import DataLoader
from facenet_pytorch import MTCNN

from photo.facedetectlib import ImageFolderCustom
from photo.models import Album, Photo


class Command(BaseCommand):
    help = "Exports album"

    def collate_fn(self, x):
        return x[0]

    def add_arguments(self, parser):
        parser.add_argument(
            '-a',
            '--album',
            dest='album',
            help='Source Album',
        )

    def handle(self, *args, **options):

        album_id = options['album']
        album = Album.objects.get(id=album_id)

        input_path = os.path.join(settings.PHOTO_ROOT, album.name[1:])
        print(input_path)

        workers = 0 if os.name == 'nt' else 4
        dataset = ImageFolderCustom(input_path)
        loader = DataLoader(dataset, collate_fn=self.collate_fn, num_workers=workers)
        device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        mtcnn = MTCNN(
            image_size=3600, margin=0, min_face_size=150,
            thresholds=[0.7, 0.8, 0.8], factor=0.709, post_process=True,
            device=device, keep_all=True
        )
        for idx, (x, y) in enumerate(loader):
            item, id = dataset.__getitem__(idx)
            filename = os.path.basename(item.filename)
            print("{}/{} processing {}".format(idx, len(loader), filename))
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
                print("{} faces found".format(len(save_boxes)))

        print("ended")
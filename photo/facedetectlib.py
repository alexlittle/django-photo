from pathlib import Path
from torch.utils.data import Dataset
from PIL import Image


class ImageFolderCustom(Dataset):

    def __init__(self, targ_dir, transform=None):
        self.paths = list(Path(targ_dir).glob("*.[jJ][pP][gG]"))
        self.transform = transform
        self.classes = sorted(list(set(map(self.get_label, self.paths))))

    @staticmethod
    def get_label(path):
        # make sure this function returns the label from the path
        return str(path.with_suffix('').name)[-1]

    def load_image(self, index):
        image_path = self.paths[index]
        return Image.open(image_path)

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, index):
        img = self.load_image(index)
        if img.mode == 'L':
            print(f"Image in grayscale, converting {img}")
            img = img.convert('RGB')
        class_name = self.get_label(self.paths[index])
        class_idx = self.classes.index(class_name)
        path = str(self.paths[index]) # get the path as string.

        if self.transform:
            print("returning transformed image")
            return self.transform(img), class_idx, path # return path too.
        else:
            print("returning img only, not transformed")
            return img, class_idx, path # return path too.
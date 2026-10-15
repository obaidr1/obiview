"""Previewable batch conversions; originals are never renamed or overwritten."""
from dataclasses import dataclass
from pathlib import Path
import shutil
import string
from image_model import ImageModel, FORMATS, atomic_write


@dataclass(frozen=True)
class BatchItem:
    source: Path
    destination: Path


def plan_batch(sources, destination, extension='.png', pattern='{stem}', start=1):
    destination = Path(destination).absolute()
    if not destination.is_dir():
        raise ValueError('Der Zielordner muss existieren.')
    if extension != 'copy' and extension.lower() not in FORMATS:
        raise ValueError('Unbekanntes Ausgabeformat')
    for _literal, field, spec, conversion in string.Formatter().parse(pattern):
        if field is not None and (field not in ('stem','index') or conversion or
                                  (spec and (field != 'index' or not __import__('re').fullmatch(r'0?[1-9]?[0-9]?d',spec)))):
            raise ValueError('Erlaubte Platzhalter: {stem}, {index}, {index:04d}.')
    result, seen = [], set()
    for index, source in enumerate(sources, int(start)):
        source = Path(source).absolute()
        if not source.is_file():
            raise ValueError(f'Quelldatei fehlt: {source}')
        stem = pattern.format(stem=source.stem, index=index)
        if not stem or stem in ('.','..') or '/' in stem or '\\' in stem or '\0' in stem:
            raise ValueError('Die Namensvorlage muss einen einfachen Dateinamen erzeugen.')
        target = destination / (stem + (source.suffix if extension == 'copy' else extension.lower()))
        key = str(target).casefold()
        if key in seen or target.exists() or target.is_symlink() or target.resolve() == source.resolve():
            raise ValueError(f'Namenskollision: {target.name}. Vorlage oder Zielordner ändern.')
        seen.add(key)
        result.append(BatchItem(source, target))
    if not result:
        raise ValueError('Keine Quelldateien gewählt.')
    return result


def run_batch(plan, *, max_width=0, max_height=0, clockwise=False,
              quality=95, metadata=True, copy_only=False, cancel=None, progress=None):
    results = []
    for item in plan:
        if cancel and cancel.is_set():
            break
        try:
            if copy_only:
                atomic_write(item.destination, lambda temp:shutil.copyfile(item.source,temp))
            else:
                model = ImageModel()
                model.load(item.source)
                if model.multiframe:
                    raise ValueError('Mehrseitige/animierte Quelle: Einzelbildverlust verhindert; separat exportieren.')
                if clockwise:
                    model.rotate()
                if max_width or max_height:
                    factor = min(1, max_width/model.image.width if max_width else 1,
                                 max_height/model.image.height if max_height else 1)
                    if factor < 1:
                        model.resize(max(1,round(model.image.width*factor)), max(1,round(model.image.height*factor)))
                model.save(item.destination, quality=quality, metadata=metadata)
            result = {'source':str(item.source), 'destination':str(item.destination), 'ok':True, 'error':None}
        except Exception as error:
            result = {'source':str(item.source), 'destination':str(item.destination), 'ok':False, 'error':str(error)}
        results.append(result)
        if progress:
            progress(len(results),len(plan),result)
    return results

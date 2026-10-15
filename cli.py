#!/usr/bin/python3
"""Headless conversion entry point using the same tested image engine."""
import argparse
import json
from pathlib import Path
from image_model import image_files
from batch import plan_batch, run_batch


def main():
    parser = argparse.ArgumentParser(description='Bildblick Stapelkonvertierung (Originale bleiben erhalten)')
    parser.add_argument('sources',nargs='+',help='Bilder oder Ordner (ohne Unterordner)')
    parser.add_argument('--output',required=True,help='Vorhandener Zielordner')
    parser.add_argument('--format',default='png',help='png, jpg, webp, tiff … oder copy')
    parser.add_argument('--pattern',default='{stem}',help='Zum Beispiel Urlaub-{index:04d}-{stem}')
    parser.add_argument('--max-width',type=int,default=0)
    parser.add_argument('--max-height',type=int,default=0)
    parser.add_argument('--quality',type=int,default=95)
    parser.add_argument('--rotate',action='store_true',help='90° im Uhrzeigersinn')
    parser.add_argument('--strip-metadata',action='store_true')
    parser.add_argument('--dry-run',action='store_true',help='Nur Dateiliste anzeigen')
    args = parser.parse_args()
    if min(args.max_width,args.max_height)<0 or not 1<=args.quality<=100:
        parser.error('Größen müssen >= 0 und Qualität zwischen 1 und 100 sein.')
    try:
        files = []
        for source in args.sources:
            path = Path(source)
            files.extend(image_files(path) if path.is_dir() else [path])
        extension = args.format if args.format=='copy' else '.'+args.format.lstrip('.')
        plan = plan_batch(files,args.output,extension,args.pattern)
        if args.dry_run:
            results = [{'source':str(p.source),'destination':str(p.destination)} for p in plan]
        else:
            results = run_batch(plan,max_width=args.max_width,max_height=args.max_height,
                quality=args.quality,clockwise=args.rotate,metadata=not args.strip_metadata,copy_only=extension=='copy')
        print(json.dumps(results,ensure_ascii=False,indent=2))
        return int(any(not r.get('ok',True) for r in results))
    except Exception as error:
        parser.exit(2,str(error)+'\n')


if __name__=='__main__':
    raise SystemExit(main())

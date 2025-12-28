# My Stash Scrapers

> This source requires the `py_common` scraper dependency. It is recommended to set the local path for this source to `community`.
> 
> Stash > Settings > Metadata Providers > Available Scrapers > <This Source> > Edit > Local Path > input `community`

## GalleryScraper

| Sites                                  | Gallery by URL | Performer by name | Performer by URL |
|:---------------------------------------|:---------------|:------------------|:-----------------|
| [E-Hentai](https://e-hentai.org)       | √              | ×                 | ×                |
| [GalleryEpic](https://galleryepic.com) | ×              | √                 | √                |
| [MissKon](https://misskon.com)         | √              | ×                 | √                |
| [V2PH](https://v2ph.com)               | √              | √                 | √                |
| [XChina](https://xchina.co)            | √              | √                 | √                |

## JavScraper

## WdTagger

> This is an experimental plugin that uses the `wd-vit` series of models to generate tags for galleries.

### How to use

> It is recommended to use a specific Python virtual environment for Stash. You can specify the Python environment in the **Stash > Settings > System > Python Executable Path**

1. install [onnxruntime-gpu](https://pypi.org/project/onnxruntime-gpu/), [huggingface-hub](https://pypi.org/project/huggingface-hub/) in the environment.
2. install the `WdTagger` scraper
3. Open the scraper's folder and modify the `config.py` file.
    - `BASE_URL`: The base URL for the stash, the default is `http://localhost:9999`
    - `MODEL`
      - The huggingface repo name, including `SmilingWolf/wd-vit-large-tagger-v3`, `SmilingWolf/wd-vit-tagger-v3`, 
      - The local model file path, e.g. `~/.cache/huggingface/hub/models--SmilingWolf--wd-vit-tagger-v3/snapshots/dc0f7f6b584d0bd3f55c4531f14ba3d4761b2bcc/model.onnx`
    - `TAG`
      - If you want to use the tags provided by the repository, use the repository name same as `MODEL`.
      - If you want to use your own tags, provide a local tag file path. e.g. `~/.cache/huggingface/hub/models--SmilingWolf--wd-vit-tagger-v3/snapshots/dc0f7f6b584d0bd3f55c4531f14ba3d4761b2bcc/selected_tags.csv`
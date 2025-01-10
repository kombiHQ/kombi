# Kombi
[![Build Status](https://travis-ci.org/kombiHQ/kombi.svg?branch=master)](https://travis-ci.org/kombiHQ/kombi)

<p align="center">
    <img src="data/ui/icons/kombi.png?v=2" with="512" height="512"/>
</p>

Kombi is focused in describing and performing tasks. These tasks can be used to wrap from executables to arbitrary python implementations. It works by providing an API that simplifies the process of describing nested tasks, passing data across tasks, handling settings for the tasks, dealing with common file system/path operations, splitting the processing and, providing interoperability across different applications bundled with python.

You may find this project useful in situations you need to combine serveral different executables/API's. For instance, during image/video processing, ingestion of files, creating/versioning data (etc).

Kombi can be used through declarative definitions to speed-up prototyping and simplify the maintainability, by reducing the need for writing boilerplate code:

<details open="true"><summary>YAML</summary>
<p>


```yaml
---
vars:
  prefix: "/tmp"
tasks:
- run: gafferScene
  metadata:
    match.types:
    - png
    match.vars:
      imageType:
      - sequence
  options:
    scene: "{configDirectory}/scene.gfr"
  target: "{prefix}/gafferBlurImageSequence/(newver <parent> as <ver>)/{name}_<ver>.(pad {frame} 6).exr"
  tasks:
  - run: ffmpeg
    options:
      frameRate: 23.976
      sourceColorSpace: bt709
      targetColorSpace: smpte170m
    target: "(dirname {filePath})/{name}.mov"
```
</p>
</details>

<details><summary>TOML</summary>
<p>

```toml
[vars]
prefix = "/tmp"

[[tasks]]
run = "gafferScene"
target = "{prefix}/gafferBlurImageSequence/(newver <parent> as <ver>)/{name}_<ver>.(pad {frame} 6).exr"

  [tasks.metadata]
  "match.types" = [
    "png"
  ]

    [tasks.metadata."match.vars"]
    imageType = [
      "sequence"
    ]

  [tasks.options]
  scene = "{configDirectory}/scene.gfr"

  [[tasks.tasks]]
  run = "ffmpeg"
  target = "(dirname {filePath})/{name}.mov"

    [tasks.tasks.options]
    frameRate = 23.976
    sourceColorSpace = "bt709"
    targetColorSpace = "smpte170m"
```
</details>

<details><summary>JSON</summary>
<p>

```json
{
  "vars": {
    "prefix": "/tmp"
  },
  "tasks": [
    {
      "run": "gafferScene",
      "metadata": {
        "match.types": [
          "png"
        ],
        "match.vars": {
          "imageType": [
            "sequence"
          ]
        }
      },
      "options": {
        "scene": "{configDirectory}/scene.gfr"
      },
      "target": "{prefix}/gafferBlurImageSequence/(newver <parent> as <ver>)/{name}_<ver>.(pad {frame} 6).exr",
      "tasks": [
        {
          "run": "ffmpeg",
          "options":{
            "frameRate": 23.976,
            "sourceColorSpace": "bt709",
            "targetColorSpace": "smpte170m"
          },
          "target": "(dirname {filePath})/{name}.mov"
        }
      ]
    }
  ]
}
```
</details>

Additionally you can run Kombi from:

<details><summary>Python</summary>
<p>

```python
# TODO
```
</details>

<details><summary>Gaffer (node-based)</summary>
<p>

```
coming soon
```
</details>

### Supported platforms
- Linux
- Mac OS
- windows

### Requirement
Python 3.5+/2.7+ 

### Optional Dependencies
Name | Version
--- | ---
Open Image IO (including python bindings/binary tools) | 1.7+
Open Color IO (including python bindings) | 1.0+
Gaffer | 0.53+
PySide | 2.0+
PyYAML | 6.0+
Qt.py | 2.4+
FFmpeg (including ffprobe) | 3.0+
nuke | 9.0+
maya | 2016+
deadline | 9.0+

## Installation

In case you are building the dependencies manually skip the step below:

### Install dependencies

<details><summary>Linux</summary>
<p>

#### Ubuntu 18.04 (bionic) and derivatives:
```bash
pip install PySide6
pip install PyYAML
pip install QtPy
apt-get install make cmake
apt-get install python3-openimageio openimageio-tools
apt-get install ffmpeg
```
</details>

<details><summary>windows</summary>
<p>

- [Cygwin](https://www.cygwin.com)
- [Python 3.6+](https://www.python.org/downloads)
- [FFmpeg](https://ffmpeg.org)
- [Qt.Py](https://pypi.org/project/QtPy)
- [PyYAML](https://pypi.org/project/PyYAML)
- [PySide2](https://pypi.org/project/PySide2)
- [Open Image IO](https://www.lfd.uci.edu/~gohlke/pythonlibs/#openimageio) (Unofficial)

</details>

### Download and unzip the release
```
# TODO
```

## Building Kombi for development

<details><summary>Details</summary>
<p>
    
> For windows users please make sure you have the posix tools available on your system. It can be done through [Cygwin](https://www.cygwin.com) (During the installation make sure to select `cmake` and `make` under `Devel` category).

#### Dependencies
Name | Version 
--- | --- 
CMake | 2.8+
Make | 3.0+
Pylama | 7.0+

#### Running tests
```bash
cd <SRC_LOCATION>
./runtest
```

#### Running linters
```bash
cd <SRC_LOCATION>
./runlint
```

#### Building Kombi
> Hint for windows users: The volumes are available under `/cygdrive/<volume>` in cygwin 

```bash
cd <SRC_LOCATION>
mkdir build
cd build
cmake -DCMAKE_INSTALL_PREFIX=<TARGET_LOCATION> -G "Unix Makefiles" ..
make all install
```

</details>

## Running 
The launchers are provided inside of the "bin" directory found inside of the installation.

Kombi command-line:
```bash
kombi --help
```

Kombi file picker tool:
```bash
kombi-gui
```
<img src="data/doc/kombi-gui-screenshot.png?v=2"/>

## Licensing
Kombi is free software; you can redistribute it and/or modify it under the terms of the MIT License

# Kombi
[![Build Status](https://travis-ci.org/kombiHQ/kombi.svg?branch=master)](https://travis-ci.org/kombiHQ/kombi)

<p align="center">
    <img src="data/ui/icons/kombi.png?v=2" with="512" height="512"/>
</p>

Kombi is a library designed to simplify the process of describing and executing tasks. It enables you to wrap from executables to custom Python implementations, providing an API that facilitates:

- Describing complex, nested tasks
- Passing data seamlessly between tasks
- Managing task settings
- Handling common file system and path operations
- Distributing processing workloads
- Enabling interoperability across various python-based applications

Kombi is especially useful for automating and integrating various executables or APIs, optimizing workflows in tasks like image and video processing, file ingestion, data creation and versioning, and more.

By leveraging declarative definitions, Kombi accelerates prototyping and simplifies maintenance by reducing the need for boilerplate code:

<details><summary>YAML</summary>
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

Running kombi:

<details><summary>Loading and running configs via the API (recommended)</summary>
<p>

```python
import os
import pathlib
from kombi.Element import Element
from kombi.TaskHolder.Loader import Loader
from kombi.Dispatcher import Dispatcher

# ensure the Gaffer executable is set correctly
# replace <GAFFER_LOCATION> with the path where Gaffer is installed (also, make sure ffmpeg is provided on your PATH)
if 'KOMBI_GAFFER_EXECUTABLE' not in os.environ:
    os.environ['KOMBI_GAFFER_EXECUTABLE'] = '<GAFFER_LOCATION>/bin/gaffer'

# this data data is shipped with kombi under <kombi/data/examples/gafferBlurImageSequence>
gafferBlurImageSequenceExampleDirectory = pathlib.Path("<KOMBI>/data/examples/gafferBlurImageSequence")

# looking for all image sequences Path objects that we are interested as input
imageSequencePaths = gafferBlurImageSequenceExampleDirectory.joinpath("imageSequence").glob("*.png")

# creating elements based on the Path objects which will be used as input for the tasks.
imageSequenceElements = map(Element.create, imageSequencePaths)

# loading tasks defined based on a config
taskHolderLoader = Loader()
taskHolderLoader.loadFromFile(gafferBlurImageSequenceExampleDirectory.joinpath('config.json'))

# executing task holder through a dispatcher (kombi provides many ways to execute it)
dispatcher = Dispatcher.create('local')
for taskHolder in taskHolderLoader.taskHolders():
    dispatcher.dispatch(taskHolder, imageSequenceElements)
```
</details>

<details><summary>Implementation of the example above using only python</summary>
<p>

```python
import os
import pathlib
from kombi.Element import Element
from kombi.Task import Task
from kombi.Template import Template
from kombi.TaskHolder import TaskHolder
from kombi.Dispatcher import Dispatcher

# ensure the Gaffer executable is set correctly by replacing <GAFFER_LOCATION> with the path where
# Gaffer (gafferhq.org) is installed. Also, make sure ffmpeg is provided on your PATH. 
# Otherwise, use the environment KOMBI_FFMPEG_EXECUTABLE to define the location of the ffmpeg executable.
if 'KOMBI_GAFFER_EXECUTABLE' not in os.environ:
    os.environ['KOMBI_GAFFER_EXECUTABLE'] = '<GAFFER_LOCATION>/bin/gaffer'

# define the directory containing the example data for the Gaffer blur image sequence
gafferBlurImageSequenceExampleDirectory = pathlib.Path("<KOMBI>/data/examples/gafferBlurImageSequence")

# retrieve all image sequence paths (PNG files) in the specified directory
imageSequencePaths = gafferBlurImageSequenceExampleDirectory.joinpath("imageSequence").glob("*.png")

# create Element objects for each image sequence path to be used as input for the tasks
imageSequenceElements = map(Element.create, imageSequencePaths)

# create the gaffer scene task
gafferSceneTask = Task.create('gafferScene')
gafferSceneTask.setOption('scene', str(gafferBlurImageSequenceExampleDirectory.joinpath('scene.gfr')))

# setting metadata (in this example we are using metadata to filter out the compatible elements)
gafferSceneTask.setMetadata(
    "match.types",
    ["png"]
)
gafferSceneTask.setMetadata(
    "match.vars.imageType", [
            "sequence"
        ]
    }
)

# create the ffmpeg task with specific options
ffmpegTask = Task.create('ffmpeg')
ffmpegTask.setOption('frameRate', 23.976)
ffmpegTask.setOption('sourceColorSpace', 'bt709')
ffmpegTask.setOption('targetColorSpace', 'smpte170m')

# since we want to define a task that will run after the gaffer scene task is done. We need to create a "Task Holder" object
# that is going to allow us to define the coupling and a few more features.
# We want also to use a template for the data that will be generated by the gaffer scene task. This template uses a built-in
# expression language made for kombi to simplify common operations (inspired by lisp).
gafferSceneTargetTemplate = Template("{prefix}/gafferBlurImageSequence/(newver <parent> as <ver>)/{name}_<ver>.(pad {frame} 6).exr")

# creating the task holder object
taskHolder = TaskHolder(gafferSceneTask, gafferSceneTargetTemplate)

# the prefix variable is not defined by the elements. Therefore, we are injecting the value for that
# (feel free to replace /tmp for another path...)
taskHolder.addVar('prefix', "/tmp")

# now creating the sub task holder that will be called when the parent task holder is done
ffmpegTargetTemplate = Template("(dirname {filePath})/{name}.mov")
taskHolder.addSubTaskHolder(TaskHolder(ffmpegTask, ffmpegTargetTemplate))

# executing task holder through a dispatcher (kombi provides many ways to execute it)
dispatcher = Dispatcher.create('local')
dispatcher.dispatch(taskHolder, imageSequenceElements)
```
</details>

<details><summary>Running configuration through kombi apps</summary>
<p>

Note: replace `<KOMBI>` for the path where kombi is provided

### Running configuration through the command-line (headless):
```bash
<KOMBI>/bin/kombi <KOMBI>/data/examples/gafferBlurImageSequence <KOMBI>/data/examples/gafferBlurImageSequence/imageSequence
```

The stdout output (task reporter) when running in headless mode is structured to facilitate easy parsing with command-line tools:
```
gafferScene		exr		/tmp/gafferBlurImageSequence/v0004/foo_def_abc_bla_001_v0004.000001.exr
gafferScene		exr		/tmp/gafferBlurImageSequence/v0004/foo_def_abc_bla_001_v0004.000002.exr
gafferScene		exr		/tmp/gafferBlurImageSequence/v0004/foo_def_abc_bla_001_v0004.000003.exr
gafferScene		exr		/tmp/gafferBlurImageSequence/v0004/foo_def_abc_bla_001_v0004.000004.exr
gafferScene		exr		/tmp/gafferBlurImageSequence/v0004/foo_def_abc_bla_001_v0004.000005.exr
gafferScene		exr		/tmp/gafferBlurImageSequence/v0004/foo_def_abc_bla_001_v0004.000006.exr
gafferScene		exr		/tmp/gafferBlurImageSequence/v0004/foo_def_abc_bla_001_v0004.000007.exr
gafferScene		exr		/tmp/gafferBlurImageSequence/v0004/foo_def_abc_bla_001_v0004.000008.exr
gafferScene		exr		/tmp/gafferBlurImageSequence/v0004/foo_def_abc_bla_001_v0004.000009.exr
gafferScene		exr		/tmp/gafferBlurImageSequence/v0004/foo_def_abc_bla_001_v0004.000010.exr
gafferScene		exr		/tmp/gafferBlurImageSequence/v0004/foo_def_abc_bla_001_v0004.000011.exr
gafferScene		exr		/tmp/gafferBlurImageSequence/v0004/foo_def_abc_bla_001_v0004.000012.exr
ffmpeg			mov		/tmp/gafferBlurImageSequence/v0004/foo_def_abc_bla_001_v0004.mov
copy			mov		/tmp/gafferBlurImageSequence/v0004/foo_def_abc_bla_001_v0004.mov_copy.mov
```

### Running configuration through the UI (kombiqt) shipped with kombi:

Note: right-click on the image sequence to list the available tasks
```bash
<KOMBI>/bin/kombi-gui <KOMBI>/data/examples/gafferBlurImageSequence <KOMBI>/data/examples/gafferBlurImageSequence/imageSequence
```
<img src="data/doc/kombi-gui-screenshot.gif?v=1"/>

The stdout output (task reporter) when running from the UI is designed to be more user-friendly:
```
gafferScene output (execution 4 seconds):
  - exr(/tmp/gafferBlurImageSequence/v0003/foo_def_abc_bla_001_v0003.000001.exr)
  - exr(/tmp/gafferBlurImageSequence/v0003/foo_def_abc_bla_001_v0003.000002.exr)
  - exr(/tmp/gafferBlurImageSequence/v0003/foo_def_abc_bla_001_v0003.000003.exr)
  - exr(/tmp/gafferBlurImageSequence/v0003/foo_def_abc_bla_001_v0003.000004.exr)
  - exr(/tmp/gafferBlurImageSequence/v0003/foo_def_abc_bla_001_v0003.000005.exr)
  - exr(/tmp/gafferBlurImageSequence/v0003/foo_def_abc_bla_001_v0003.000006.exr)
  - exr(/tmp/gafferBlurImageSequence/v0003/foo_def_abc_bla_001_v0003.000007.exr)
  - exr(/tmp/gafferBlurImageSequence/v0003/foo_def_abc_bla_001_v0003.000008.exr)
  - exr(/tmp/gafferBlurImageSequence/v0003/foo_def_abc_bla_001_v0003.000009.exr)
  - exr(/tmp/gafferBlurImageSequence/v0003/foo_def_abc_bla_001_v0003.000010.exr)
  - exr(/tmp/gafferBlurImageSequence/v0003/foo_def_abc_bla_001_v0003.000011.exr)
  - exr(/tmp/gafferBlurImageSequence/v0003/foo_def_abc_bla_001_v0003.000012.exr)
done
ffmpeg output (execution 0 seconds):
  - mov(/tmp/gafferBlurImageSequence/v0003/foo_def_abc_bla_001_v0003.mov)
done
copy output (execution 0 seconds):
  - mov(/tmp/gafferBlurImageSequence/v0003/foo_def_abc_bla_001_v0003.mov_copy.mov)
done
```
</details>

<details><summary>Scripting inside kombi</summary>
Kombi comes with a built-in script editor, which can be particularly helpful in applications that either lack an integrated script editor or have a very limited one.

Use `<ctrl>` + `<enter>` to run the code. In case there is a selection in place only the selected code will be performed.

Hit the python button to add a script-editor tab to the main interface. These tabs and their contents remain consistent across sessions:

<img src="data/doc/kombi-script-editor-button.png?v=1"/>
<br/><br/>

You can adjust the panel size as needed. The color scheme is inspired by [VIM preferences](https://github.com/paulondc/prefs/blob/master/vimNotes.md):

<img src="data/doc/kombi-script-editor.png?v=2"/>


The script editor can interact with the main window through the `mainWindow()`, which is automatically defined for the script editor session for convenience. For instance:
```python
print(mainWindow().elementListWidget().elements())
print(mainWindow().elementListWidget().selectedElements())
```
</details>

### Supported platforms
- Linux
- Mac OS
- windows

### Requirement
Python 3.7+

### Optional Dependencies
<details>
<p>

Name | Version
--- | ---
Open Image IO (including python bindings/binary tools) | 1.7+
Open Color IO (including python bindings) | 1.0+
Gaffer | 0.53+
PySide | 2.0+
PyYAML | 6.0+
Py Call Graph | 2.1+
Jedi | 0.19+
Qt.py | 2.4+
FFmpeg (including ffprobe) | 7.0+
nuke | 9.0+
maya | 2016+
deadline | 9.0+
graphviz | 12.1+
</details>

## Installation

In case you are building the dependencies manually skip the step below:

### Install dependencies

#### Python:

Note: Kombi is compatible with both `PySide2` and `PySide6`. Please use the version that best suits your requirements.
```bash
pip install PySide6 PyYAML Qt.Py python-call-graph jedi
```

Additionally, if you want to support the image processing tasks, you will need to install OpenImageIO. Otherwise, feel free to skip this step:
```
pip install oiio-static-python
```

<details><summary>Linux</summary>
<p>

#### Ubuntu and derivatives:
```bash
apt-get install ffmpeg
apt-get install graphviz
```

In recent versions of Ubuntu, you may also need to install `libxcb-cursor0` in order to use the `xcb` plugin for Qt:
```
apt install libxcb-cursor0
```
</details>

<details><summary>Windows</summary>
<p>

- [Python 3.7+](https://www.python.org/downloads)
- [FFmpeg](https://ffmpeg.org)
- [Graphviz](https://graphviz.org)
  
</details>

## Kombi Development

<details><summary>Details</summary>
<p>

#### Dependencies
Name | Version 
--- | --- 
Pylama | 7+
Setup Tools | 75+

#### Running tests
```bash
cd <SRC_LOCATION>
./runtest
```

#### Running linters
Install requirements:
```
pip install pylama setuptools
```
Run linter:
```bash
cd <SRC_LOCATION>
./runlint
```

#### Creating deployment package

```bash
cd <SRC_LOCATION>
python3 package.py
```

For advanced options please use the flag `--help`:
```bash
cd <SRC_LOCATION>
python3 package.py --help
```
</details>

## Licensing
Kombi is free software; you can redistribute it and/or modify it under the terms of the MIT License

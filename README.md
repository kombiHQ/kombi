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

By leveraging declarative definitions, Kombi accelerates prototyping and simplifies maintenance by reducing the need for boilerplate code. For more details, visit the [Wiki](https://github.com/kombiHQ/kombi/wiki).

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
apt-get install openimageio-tools
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
Setuptools | 75+
Coverage | 7.8+

Install requirements:
```
pip install pylama setuptools coverage
```

#### Running tests
Depending on the version of OpenImageIO you're using, you may need to specify an OCIO configuration. Kombi includes a basic config that can be used if needed:
```bash
export OCIO="<SRC_LOCATION>/data/thirdparty/opencolorio/config.ocio"
```

```bash
cd <SRC_LOCATION>
./runtest
```

#### Running linters
```bash
cd <SRC_LOCATION>
./runlint
```

#### Running coverage
```bash
cd <SRC_LOCATION>
./runcoverage
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

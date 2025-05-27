# Kombi
[![CI](https://github.com/kombiHQ/kombi/actions/workflows/python-package.yml/badge.svg)](https://github.com/kombiHQ/kombi/actions/workflows/python-package.yml)

<p align="center">
    <img src="src/kombiqt/resources/icons/kombi.png?v=2" with="512" height="512"/>
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

Full install (UI Support based on Pyside6):
```bash
pip install "https://github.com/kombiHQ/kombi/archive/master.zip#egg=kombi[dev,gui]"
```

Full install legacy (UI Support based on Pyside2):
```bash
pip install "https://github.com/kombiHQ/kombi/archive/master.zip#egg=kombi[dev,gui-legacy]"
```

Basic install (No UI support):
```bash
pip install "https://github.com/kombiHQ/kombi/archive/master.zip"
```

### Install dependencies

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

[Development guidelines](CONTRIBUTING.md).

<details><summary>Details</summary>
<p>

#### Dependencies
Install requirements:
```bash
pip install "https://github.com/kombiHQ/kombi/archive/master.zip#egg=kombi[dev]"
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

</details>

## Licensing
Kombi is free software; you can redistribute it and/or modify it under the terms of the [MIT License](LICENSE)

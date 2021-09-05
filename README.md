# Dofus treasure finder

![A nice chest.](./assets/icon.png)

## Description 

A Python script that finds the current treasure hunt hint.

This software doesn't automatically solve the treasure hunt but only simplify the use of [Dofus Map](https://dofus-map.com/hunt). As Dofus Map does not seem to be prohibited by Ankama and as this software doesn't interact with the game memory or packets, you shouldn't have any issue using this. Also keep in mind that both this script and Dofus Map aren't 100% reliable.

*Only available for Windows.*

## How to use it

Download the latest release and launch the application using `dtf.exe`. You may want to create a shortcut for future uses.

## Building

### Requirements

You need to install the following Python packages using [pypi](https://pypi.org/project/pip/) :

* `python-Levenshtein` ;
* `pytesseract` ;
* `pywin32` ;
* `requests` :
* `fuzzywuzzy` ;
* `pyinstaller` ;

You also need to install the following software :

* [Visual C++ Build Tools](https://visualstudio.microsoft.com/fr/downloads/) through the Visual Studio Installer for instance ;
* [Tesseract](https://github.com/tesseract-ocr/tesseract/releases) through Github, also remember to set the right environment variable as explained in Tesseract's documentation ;

To get the pre-packaged Tesseract version to put with the build you can either get the `tesseract.exe` file provided in the latest release or [build the static version yourself](https://tesseract-ocr.github.io/tessdoc/Compiling.html#windows).

### Actually building

First, you need to setup the `dtf.spec` file, the file `dtf.spec.example` gives the general aspect of it. You need to modify the lines 8 and 9 to match your directories.

For more informations on how this file works, [go here](https://pyinstaller.readthedocs.io/en/stable/spec-files.html).

Then, to build the software, use the following command :

```
pyinstaller dtf.spec
```

The `.exe` file is then available under the directory `./dist/dtf/`.

## How it works

The Dofus window is captured as an image to extract the location and hints data using [OCR](https://en.wikipedia.org/wiki/Optical_character_recognition). Then, the hints available in each directions are grabbed through [Dofus Map](https://dofus-map.com/hunt). Enventually, the hints found are matched to that list and the most likely hint in each direction is displayed.

## License

You can do whatever you want with this. It would be nice to cite me as a reference if you use parts of my code.

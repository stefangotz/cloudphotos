# cloudphotos

Import photos and videos from iCloud into Windows without the hassle.

With iCloud for Windows installed, this application downloads all iCloud photos and videos, copies them to an import folder on your computer, and converts HEIC images to JPEG images.

## Setup

1. Install iCloud for Windows
2. Install [ImageMagick](imagemagick.org)
3. Install [Python](python.org)
4. Install dependencies:

    `pip install --user --upgrade pip exifread pydantic`

## Run

`py -m cloudfiles ICLOUD_PHOTOS_DIR DESTINATION_DIR`

## Development

Improvements to the code are most welcome.

To get started with this Python project, note that it relies on a number of fairly common Python tools to improve the development experience, first and foremost being *poetry*.
The script `tools/setup.sh` contains the instructions to initialise a development environment for this project.
If on Windows, try running it from a *git bash* session or simply run the commands it contains on the command prompt or a powershell session.

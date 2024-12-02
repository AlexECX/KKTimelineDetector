# KKTimelineDetector

A tool for detecting whether scene data in Koikatsu (or Koikatsu Sunshine) contains timeline information. This detector is capable of distinguishing static images with timeline data and currently exists in both desktop and web versions.

## Versions Available

### Desktop Version (exe_ver)
A standalone Python application built with tkinter, providing a desktop interface for timeline detection.

Download the latest release [here](https://github.com/GameProgram777/KKTimelineDetector/releases)


### Web Version (web_ver)
A web-based version built with PyScript, providing the same functionality through a browser interface.

#### Live Demo
Access the web version here: https://GameProgram777.github.io/KKTimelineDetector/web_ver/

## Features
- Detects presence of timeline in scene data files
- Distinguishes between static and dynamic images
- Identifies GIF (duration ≤ 10s) and movie (duration > 10s) content
- Supports .png file format
- Drag and drop interface

## Current Classification Method

The detector uses string matching to identify different types of scene data:

1. First Level: Timeline Presence
   - Checks for "timeline" string in the content
   - If found: classified as "has timeline"
   - If not found: classified as "no timeline"

2. Second Level (for "has timeline" content):
   - If only "timeline" is found: classified as static image
   - If both "timeline" and "Timeline" are found: classified as dynamic content
   - For dynamic content, duration is extracted to determine if it's a GIF (≤10s) or movie (>10s)

## Known Limitations and Areas for Improvement

1. **Classification of Scenes Without Timeline Data**  
   - **Current Issue:** There is currently no effective method to differentiate between static and dynamic scenes in files without timeline data (which are predominantly static).  
   - **Improvement Needed:** Investigate and implement alternative techniques to accurately identify motion or animation in these files.

2. **Distinguishing Static and Dynamic Timeline Data**  
   - **Current Method:** The tool uses string matching between "timeline" and "Timeline" to differentiate static from dynamic scenes in files with timeline data (which are mostly dynamic).  
   - **Limitation:** While this approach is generally effective, there are occasional misclassifications in certain edge cases.  
   - **Improvement Needed:** Develop a more robust method for distinguishing between static and dynamic scenes to enhance classification accuracy.

If you have insights into more accurate detection methods or understand the underlying file structure that could provide better classification, please:
- Open an issue on GitHub
- Submit a pull request with improvements
- Contact me with your findings

Your contributions to improving the accuracy of this tool would be greatly appreciated!


## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
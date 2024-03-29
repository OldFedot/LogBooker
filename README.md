LogBooker
======
Researchgate link: 
https://www.researchgate.net/publication/370682290_Logbooker_-_software_for_easy_management_summarizing_and_extracting_information_from_crystallographic_information_files
<img width="677" alt="1" src="https://github.com/OldFedot/LogBooker/assets/149039437/34b82845-ac7e-44ba-b8f4-d3f0adb00975">

Time saving software for easy management, summarizing and extracting information fromcrystallographic information files (.CIF) coming from single crystal XRD data analysis.
### Basic principle
- Track the file system for existence, appearance and update of cif files
- Extraction of essential information (such as symmetry, unit cell parameters,refinement details, atomic coordinates, bond distances etc.) from a bunch of cif files
- Write down all extracted information to a single, well structured, MS Excel file
  <img width="535" alt="1" src="https://github.com/OldFedot/LogBooker/assets/149039437/63aa085a-9aa8-4067-b1eb-ac018a4da2ac">

### Operation
- Static mode: allows single search for the all cif files in specified folder and savinginformation to the MS Excel file. Normally, this mode is used to prepare asummary from a processed single crystal data 
- Live mode: tracking updates of files in real time. The mostly useful during dataprocessing (integration, structure solution and refinement)

Look into user manual for more details

### Compatibility
So far, Logbooker is designed to work with .cif files generated by CrysAlisPro, Jana2006 and Olex2. However, it can work with files generated by other softwares, but depending on the origin it can rarely cause the crash of the program 

Maintainer
----------
Timofey Fedotenko (timofeyfedotenko@gmail.com)


Requirements
----------
Python 3.10 and above

### Executables
Executable versions for Windows can be downloaded from:
https://drive.google.com/drive/folders/1R89FC13sJoqwdZEumzl0THt5jhyYb31X?usp=drive_link


### Code
In order to make changes to the source code yourself or always get the latest development versions you need to install
the required python packages on your machine.

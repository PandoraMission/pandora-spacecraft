# Installing Spice

In order to use some of the functionality in pandora-spacecraft, you will need to have CSPICE and spiceypy installed. Here are the instructions to do so on a Mac with an M1 chip.

NOTE (7/14/2026): This guide is currently incomplete. It will be updated with further information on installing `ckslicer` soon.



1. Download the following files from [the NAIF website](https://naif.jpl.nasa.gov/naif/toolkit_C_MacM1_OSX_clang_64bit.html).
    ```
	cspice.tar.Z
	importCSpice.csh
    ```
   This page also contains a helpful README which contains more information about the installation process.

2. Place these files in your root directory on your computer.

3. In the terminal, run
	```
    /bin/csh -f importCSpice.csh
    ```
   The script importCSpice.csh will uncompress and untar the toolkit and,
   on platforms where NAIF anticipates that it is necessary, compile and
   link all source code products. It should create a cspice/ directory in the location that you placed the original files.

4. Open your .zshrc file and add the line:
	```
    export PATH="$HOME/cspice/exe:$PATH"
    ```
   Adjust as needed to reflect the path where your cspice/ directory lives.

5. Open a fresh terminal and You can also check that cspice itself is working with the command
	```
    tobin cook__01.tsp
    ```

6. Install spiceypy in the python environment of your choosing. e.g.
	```
    poetry install spiceypy
    ```

7. Check that spiceypy is finding cspice correctly with
	```
    which msopck
    ```
   If this fails, you have likely inputed the wrong path in your .zshrc file.

8. You'll also need to install the utility ckslicer, which can be downloaded from [the NAIF utilities page](https://naif.jpl.nasa.gov/naif/utilities_PC_Linux_32bit.html). Download the file by clicking "ckslicer" in the table, then place the file in `cspice/exe/`. 

    NOTE: If you are on a government computer, you will need elevated privileges on your machine in order to install this executable. You may need to submit a NAMS request to complete this step.



If everything working you should be good to go!

You can find additional documentation on the [NAIF website](https://naif.jpl.nasa.gov/naif/toolkit.html) or look at their [Toolkit installation slides](https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/Tutorials/pdf/individual_docs/07_installing_toolkit.pdf)

# Installing Spice

In order to use some of the functionality in pandora-spacecraft, you will need to have CSPICE and spiceypy installed. This is primarily needed for people involved in maintaining this package or uploading new SPK/TLEs. Here are the instructions to do so on a Mac with an M1 chip.

You can find additional documentation on the [NAIF website](https://naif.jpl.nasa.gov/naif/toolkit.html) or look at their [Toolkit installation slides](https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/Tutorials/pdf/individual_docs/07_installing_toolkit.pdf).




1. Download the following files from [the NAIF website](https://naif.jpl.nasa.gov/naif/toolkit_C_MacM1_OSX_clang_64bit.html).
    ```
	cspice.tar.Z
	importCSpice.csh
    ```
   This page also contains a helpful README which contains more information about the installation process.

2. Place these files in your root directory on your computer.

3. In the terminal, navigate to your root directory and run
	```
    /bin/csh -f importCSpice.csh
    ```
   The script `importCSpice.csh` will uncompress and untar the toolkit and,
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

8. You'll also need to install the utility `ckslicer`, which can be downloaded from [the NAIF utilities page](https://naif.jpl.nasa.gov/naif/utilities_PC_Linux_32bit.html). Download the file by clicking "ckslicer" in the table, then place the file in `cspice/exe/`. 

    **NOTE:** If you are on a government computer, you will need elevated privileges on your machine in order to install this executable. You may need to submit a NAMS request to complete this step.

    8a. Place the `ckslicer` file in in `cspice/exe/`. Run chmod to make the downladed file executable.
    ```
    chmod +x ~/cspice/exe/ckslicer
    ```

    8b. Navigate to your cspice directory and run
    ```
    /bin/csh -f makeall.csh
    ```

    8c. At this point, check if you are able to run the commands in `maintainers.md`. If you are--great, you're all done! If not (especially if you are working on a government computer), you may need to check that a) you have elevated privileges on your computer and b) whether there is a software quarantine on `ckslicer`. The first must be resolved by submitting a NAMS request, and the latter can be resolved with a to visit the IT department. Once you have cleared up those issues, run step 8b again and you should be good to go.


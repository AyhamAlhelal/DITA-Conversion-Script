# DITA Conversion Script

## Instructions

### One-Time Setup
These steps only need to be done once before using the script.

1. Install **Inkscape 1.4**
2. Install **GhostScript 10.04.0**
3. Install **ImageMagick 7.1.1**
4. Add the following paths to the **Environment Variables**:
   - `C:\Program Files\Inkscape\bin`
   - `C:\Program Files\gs\gs10.04.0\bin`
   - `C:\Program Files\gs\gs10.04.0\lib`
   - `C:\Program Files\ImageMagick-7.1.1-Q16-HDRI`
   - `C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\lib`

---

### Steps to Run the Script
These steps must be followed every time you need to use the script.

5. Place the content in the `./in` folder and delete everything in the `./out` folder.
6. Open **oXygen** and load `task.pr`.
7. In **oXygen**, right-click the `in` folder, select **Transform > Transform with**, and then choose **mtask**.
8. After the previous step is complete, double-click the script **namespace.bat**.
9. Double-click the script **epsToSvg.bat**.
10. Double-click the script **tiffToPng.bat**.
11. Check the results in the `out` folder.

---

### Notes
- Ensure all required software is properly installed and configured before running the script.
- If you encounter any issues, verify the environment variable paths and software installations.


"""
Stable Collector by Artemonim, 2023
Designed to navigate through a collection of images generated by Stable Diffusion.

Changelog:
    v0.0.03-alpha:
        index as json, not as python lists
        We broke "Building grid..." process, yay!
        Multiple fixes and refactoring

    v0.1.00-beta:
        TODO: GUI
        TODO: Add normal album viewer
        TODO: Add image viewer
        TODO: Add image metadata viewer
        TODO: Make it .executable
        TODO: Change path to the outputs folder trough the UI
        TODO: Enter a query trough the UI
        True indexation
        TODO: "Rebuild index" button
        TODO: Log file

Known issues:
    - Non-adaptive aspect ratio
    - Grid images oversize error (suppressed by MAX_IMAGE_PIXELS)
    - Indexation is not working properly - some images are not indexed (see "no parameters found")
    - Grid of images are not shown - need to rewrite "Building grid..." process

Future plans:
    - Settings menu
    - Set type of images to search for (grid, image)
    - Negative query (blacklist)
    - Copy found images to a new folder
    - Export images with watermark
    - Export images in optimized format

Dependencies:
    - PIL (Pillow)
    - tkinter
    - simplejson (optional)
"""

import os
import time
from random import random

import PIL.Image as Image
import PIL.ImageTk as ImageTk
import tkinter as tk
try:
    import simplejson as json   # Faster or newer than json
except ImportError:
    import json

# Constants
SD_METADATA = ("extras", "parameters", "postprocessing")    # Metadata keys that are used in Stable Diffusion (full?)

# TEST VARIABLES    # TODO: Change this trough the UI in debug mode
LIMITER: int = 0 - 1    # It's a limit for the number of files to be indexed. Set to -1 to disable. Must be x - 1
DO_NOT_OPEN = False     # If True, then the program will not open the window with the results
AUTO_CLOSE: int = 5     # If not 0, then the program will close the window with the results after AUTO_CLOSE seconds
Image.MAX_IMAGE_PIXELS = None   # TODO: Rewrite this so it doesn't disable protection completely
TEST_QUERIES = ("jacket", "shirt", "hair", "face")

# settings variables    # TODO: Change this trough the UI and save it to a file
searchAreaPath = "D:/Stable UI/stable-diffusion-webui/outputs/"  # Path to the folder with images
dontSearchForGrids = True   # If True, then the program will not search for grid images
resetIndexOnStart = True    # If True, then the program will reset the index.json on start

# Global variables
pngs = {}   # List of pngs in the search area


def getPNGs(path):
    files = os.listdir(path)
    for file in files:
        if 0 <= LIMITER < len(pngs):
            return
        if dontSearchForGrids:
            if "grid" in file:
                continue

        local_path = os.path.join(path, file).replace("\\", "/")

        # Check if file is a folder
        if os.path.isdir(os.path.join(path, file)):
            # If it is a folder, then call the getPNGs function again
            print("Folder found: " + local_path)    # TODO: log this
            getPNGs(os.path.join(path, file))
        elif file.endswith(".png"):
            if local_path not in pngs:
                print("PNG found: " + local_path)   # TODO: log this
                pngs[local_path], processing_errors = imageParametersSplitter(local_path)
                if processing_errors:
                    pass    # TODO: Inform the user about the errors

def isItGrid(line):
    # check if line have word "grid" in it
    if "grid" in line:
        return True


def imageParametersSplitter(path):
    """
    Splits image parameters by keywords and returns a dict of them
    :param path: system path to image
    :return: dict of parameters, bool of processing errors
    """
    try:
        info = str(Image.open(path).info["parameters"])
    except KeyError:
        print("KeyError: " + path)  # TODO: log this
        return "Error processing metadata: no parameters found", True
    info_dict = {}
    try:
        if info.find("\nNegative prompt:") != -1:
            info_dict.update({"prompt": info[:info.index("\nNegative prompt:")]})
            info_dict.update({"negative_prompt": info[info.index("\nNegative prompt:")+17:info.index("\nSteps:")]})
        else:
            info_dict.update({"prompt": info[:info.index("\nSteps:")]})
        info_dict.update({"steps": info[info.index("\nSteps: ")+8:info.index("Sampler:")-2]})
        info_dict.update({"sampler": info[info.index("Sampler: ")+9:info.index("CFG scale:")-2]})
        info_dict.update({"cfg_scale": info[info.index("CFG scale: ")+11:info.index("Seed:")-2]})
        if info.find("Face restoration:") != -1:
            info_dict.update({"seed": info[info.index("Seed: ")+6:info.index("Face restoration:")-2]})
            info_dict.update({"face_restoration": info[info.index("Face restoration: ")+18:info.index("Size:")-2]})
        else:
            info_dict.update({"seed": info[info.index("Seed: ") + 6:info.index("Size:") - 2]})
        info_dict.update({"size": info[info.index("Size: ")+6:info.index("Model hash:")-2]})
        if info.find("Hires upscaler:") != -1:
            info_dict.update({"model": info[info.index("Model: ") + 8:info.index("Denoising strength:") - 2]})
            info_dict.update({"denoising_strength": info[info.index("Denoising strength: ")+20
                                                         :info.index("Hires upscale:")-2]})
            info_dict.update({"hires_upscale": info[info.index("Hires upscale: ")+15:info.index("Hires steps:")-2]})
            info_dict.update({"hires_steps": info[info.index("Hires steps: ")+13:info.index("Hires upscaler:")-2]})
            info_dict.update({"hires_upscaler": info[info.index("Hires upscaler: ")+16:]})
        else:
            info_dict.update({"model": info[info.index("Model: ") + 8:]})
    except ValueError:
        print("Error processing metadata: " + path)     # TODO: log this
        return "Error processing metadata: broken parameters", True
    return info_dict, False


# Import png files through PIL
if __name__ == '__main__':
    searchArea = os.listdir(searchAreaPath)
    i = 0
    print("Start working!")
    start_time = time.time()    # TEST: Start time of execution

    # Save pngs to json file
    with open('Index/index.json', 'r+') as f:
        if resetIndexOnStart:
            print("Resetting index...")
            f.truncate()
        else:
            # check if json file is empty
            if os.stat('Index/index.json').st_size != 0:
                pngs = json.load(f)
        getPNGs(searchAreaPath)
        json.dump(pngs, f, indent=4)

        print("\nIndexation done!")
        print(len(pngs), "files found!")

        # Read json file with pngs
        # check if pngs list is empty
        if len(pngs) == 0:
            data = json.load(f)
        else:
            data = pngs
        # read first file in the json file and print its metadata in pretty format
        # print(json.dumps(Image.open(data[0]).info, indent=4, sort_keys=True))     # TEST: Print metadata

        # pick query from TEST_QUERIES randomly     # TODO: Change this trough the UI
        query = TEST_QUERIES[int(random() * len(TEST_QUERIES))]
        # query = "cat"
        print("Query:", query)
        results = []
        for file in data:
            try:
                for line in file[1]:
                    if query in line:    # Look SD_METADATA for metadata keys
                        print(file)
                        results.append(file[0])
                        break
            except:
                print("Error: " + file[0])
                pass

        # Show results images in tkinter window as a grid
        root = tk.Tk()
        root.title("Stable Collector: " + query + " results")
        windowWidth = 1600
        windowHeight = 800
        targetImageWidth = 200
        targetImageHeight = 200
        root.geometry(f"{windowWidth}x{windowHeight}+0+0")
        root.resizable(True, True)

        print("Building grid...")
        for i in range(len(results)):
            img = ImageTk.PhotoImage(Image.open(results[i]).resize((targetImageWidth, targetImageHeight)))
            panel = tk.Label(root, image=img)
            panel.image = img
            panel.grid(row=i//(windowWidth//targetImageWidth), column=i%(windowWidth//targetImageWidth))

        if not DO_NOT_OPEN:
            print("Opening window...")
            if AUTO_CLOSE != 0:
                print("Closing window in", AUTO_CLOSE, "seconds...")
                root.after(AUTO_CLOSE * 1000, lambda: root.destroy())

            print("--- %s seconds ---" % (time.time() - start_time))  # TEST: Print time of execution
            root.mainloop()




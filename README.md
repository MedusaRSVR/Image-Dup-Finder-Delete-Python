# Image-Dup-Finder-Delete-Python
With this tool you can select a folder and let it find duplicate images within it, mark and delete them. It also takes sub-folders into consideration.

Created with Ollama and the NeuralQuantum-Coder
https://ollama.com/NeuroEquality/neuralquantum-coder

1. Clone Repository
2. Run setup_dedup.bat to create a VENV and install the requirements.txt
3. Run run_dedup.bat

It uses 

All duplicate immages will have a different color
- green = first duplicate
- yellow = second duplicate
- orange = third duplicate
- red = fourth duplicate

I didn't added more colors. Every other duplicate found will have a plain gray.

On top of the UI you can select the checkbox related to the color you want to mark and delete. Once selected click on "Delete Selected".
It doesn't use the Recycle Bin. It just delete the image-duplicates.
You've been warned.

Why i created it?
I have ACDSee installed and it's Duplicate-Finder isn't as powerfull as i wished it would.
I have tons of images on my pc due to the excessive use of Stable Diffusion Checkpoint-/LoRa-Training and i wanted to have a good tool to get rid of the duplicates.
That's why... Have fun...

*Tested with folders that contained more than 100k images.

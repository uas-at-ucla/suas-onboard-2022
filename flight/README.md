# suas-onboard/flight
Instructions and scripts for installing 'stuff' for SUAS flight

## Python3.9
---

### **Install python3.9 on Linux (Ubuntu)**
Run the following script in terminal
```bash
sudo apt install python3
```
### **Install python3.9 on Windows**
Go to https://www.python.org/downloads/, then download and install python 3.9.13. 

i.e. 
1. Look for python 3.9.13
2. click download
3. choose the installer that matches your machine specs
4. download it
5. run installation
6. complete installation.
### **Install python3.9 on MacOS**
Install homebrew (the package manager, not a coffee preparation heuristic) by running the following script in your terminal
``` bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Then, restart your terminal and run the following script
``` bash
brew install python3
brew install pyenv
pyenv install 3.9.13
```
## ArduPlane
---

### **Using Docker**

(WIP) If you'd like to install this software using Docker, then you can! Just follow the following steps below for your respective machine:

#### **MAC / Linux**

1. Download and install Docker for your respective machine. Link found [here](https://docs.docker.com/get-docker/). 
2. Once downloaded, clone the following repository in the current folder (i.e. suas-onboard/flight): https://github.com/ggharibian/ardupilot-suas
3. Run the 

#### **Windows**
**[WIP]**

### **Using a Virtual Machine / WSL2**

ArduPlane is a version of PX4's simulation software used in order to visualize the drone flying while you work on your code / sub-project. The downside is that **you may only be able to run this on a ubuntu machine (or, in the case of windows, using WSL2 / Cygwin)**. Therefore, either a virtual machine must be installed on your system, or a sub-system os (such as cygwin, wsl2, etc.) must be running on your device in order for you to install this software. Once this is available, follow the following steps to complete the installation.

1. Open your linux terminal (either wsl2, cygwin, or your terminal in your virtual machine)
2. Run the provided **ubuntu_arduplane_install.sh** script in the terminal, using the following command: 
    ``` bash
        bash ubuntu_arduplane_install.sh
    ```
    - If you're running wsl2, you should be able to navigate to the folder where this file is using ```cd```, then run the script. 
    - For **virtual machine users**, it may be easier to either open the script, and copy the contents into your terminal, and run each line individually. Or, for the brave of heart, 
        1. Install git on the linux installation using the terminal using the following command
            ``` bash
                sudo apt install git
            ```
        2. Clone this repo in the virtual machine, using the following command
            ```
            git clone https://github.com/uas-at-ucla/SUAS-Installs.git
            ```
        3. Run the following to go into the directory, and run the installer.
            ```
            cd SUAS-Installs
            bash ubuntu_arduplane_install.sh
            ```

**NOTE: This installation takes A WHILE.**

## VcXsrv
---
**NOTE: Needed for WSL2 on Windows 10 ONLY**

The ArduPlane simulator will run on WSL, but to access the graphical simulation, we need to tell
WSL to port the graphics to the Windows host system.
To do this, we use an VcXsrv server to receive the graphics.

To install VcXsrv, follow the instructions [here](https://sourceforge.net/projects/vcxsrv/)

This will create a program called XLaunch which will launch the VcXsrv server.

### **To set the needed window parameter correctly, and run XLaunch**
Run the following lines to the end of your ~/.bashrc file using wsl2
``` bash
export DISPLAY=$(ip route list default | awk '{print $3}'):0
export LIBGL_ALWAYS_INDIRECT=1
```
Then run XLaunch. While running, simply keep the default settings at all pages except the second-to-last one. Here, make sure to check the **"disable access control"** box. Then, finish the run.

## Python Virtual Environment
---
To manage our Python libraries, we use Pip3.
However, we also want a program to isolate our workspaces so we don't use include packages from other workspaces.
The solution to this is a Python virtual environment (venv).
<br/>

### Create the virtual environment
To create a Python virtual environment, do
```bash
python -m venv venv
```
which creates a virtual environment folder called 'venv'.
<br/>

### Activating the virtual environment
To activate a Python virtual environment, do
```bash
source ./venv/bin/activate
```
which runs the activation script. 
Your lines in the terminal should now start with '(venv)'.
<br/>

### Installing required packages
To install required packages, do
```bash
pip3 install -r requirements.txt
```
which installs all the packages from requirements.txt into the virtual environment.
This allows us to document the packages we are using for this specific workspace.


## VSCode (recommended)
---
Now that we have all the frameworks and packages we want to use, we need a place to actually write ***CODE***.
For this, we use a type of software called an *Integrate Development Environment* or *IDE* for short.
This is basically a fancy text editor made specifically to write code. 
We recommend using VSCode for our projects. VSCode allows for a lot of customization and sharing them.

You can find VSCode [here](https://code.visualstudio.com/Download)

**TBD: VSCode extension and configuration**

## Windows Terminal (recommended)
---
Windows terminal is Microsoft's terminal application. It allows you to run any terminal instance (wsl2, cygwin, putty, powershell, command line, etc.) from the same program. It's also highly customizable. Highly recommend for Windows users!!
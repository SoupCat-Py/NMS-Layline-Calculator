# NMS-LC v3
# version 3.3.0

'''
PATCH NOTES:
• added the "view code" button that goes to the .py file on GitHub
• modified the commands for the "contact me" and "video tutorial" buttons
• slight (non-functional) update to the "calculate" function
'''

# UI
import customtkinter as ctk         # general GUI library
import tkinter as tk                # menu bar
from tkinter import filedialog      # path
from PIL import Image               # button icons
import tkinter.messagebox as msg    # showing errors
# utilities
import math, os, sys, subprocess
import webbrowser as web
import datetime as dt


path=None
calcDone = False
nms='GeosansLight-NMS'


def resource_path(relative_path):
    # Get absolute path to resource, works for dev and packaged app
    try:
        # When running as a packaged executable
        base_path = sys._MEIPASS
    except AttributeError:
        # When running in the development environment
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def writable_path(relative_path):
    # Get path to writable resource stored in user's home directory.
    user_data_dir = os.path.join(os.path.expanduser("~"), "NMSLC_Data")
    os.makedirs(user_data_dir, exist_ok=True)
    return os.path.join(user_data_dir, relative_path)

def initialize_writable_files():
    # Copy writable files to user directory if not already present.
    files_to_copy = ["mode.txt", "crash_log.txt"]
    for file in files_to_copy:
        source_path = resource_path(f"Text/{file}")
        dest_path = writable_path(file)
        if not os.path.exists(dest_path):
            try:
                with open(source_path, "r") as src, open(dest_path, "w") as dst:
                    dst.write(src.read())
            except Exception as e:
                msg.showerror('Unexpected Error!', f'Error copying {file}: {e}')

# Call this function at the start of your app
initialize_writable_files()



# Suppress Windows error reporting dialogs
if os.name == "nt":  # Only for Windows
    import ctypes
    SEM_NOGPFAULTERRORBOX = 0x0002
    ctypes.windll.kernel32.SetErrorMode(SEM_NOGPFAULTERRORBOX)





def calculate(lat1, lat2, long1, long2, distance):
    global calcDone, verticalResult
    calcDone = True # set this for the program to know if a calc has been completed
    laylineDistance = (655*math.sqrt((lat2-lat1)**2 + (long2-long1)**2)) / distance # super special formula

    # add/subtract laylineDistance from major angles
    angles = [-90, 0, 90, 180]
    listAdd = [angle + (laylineDistance/2) for angle in angles]
    listSubtract = [angle - (laylineDistance/2) for angle in angles]

    # combine both lists into one
    listResult = listAdd + listSubtract

    # check for values >180 or <180 to change the sign
    for i in range (len(listResult)):
        if listResult[i] > 180:
            listResult[i] -= 360
        if listResult[i] < -180:
            listResult[i] += 360
        listResult[i] = round(listResult[i], 2)

    listResult.sort()  # sort list
    verticalResult = "\n".join(map(str, listResult))  # turn the list into a vertically-formatted string
    return verticalResult

# make a blank text file
def makeNew():
    global path

    # make initial name
    newFileName = defaultFileName = 'laylines'
    app.confirm_label.configure(text='Generating file...', text_color='yellow')

    def join(name):
        newPath = os.path.join(os.path.expanduser('~/Downloads'), f'{name}.txt')
        return newPath

    # check if file is already in user's downloads
    def check():
        pathCheck = join(newFileName)
        if os.path.exists(pathCheck):
            exists = True
        else:
            exists = False
        return exists
    
    exists = check()
    if exists:
        index = 1
    while exists:
        newFileName = f'{defaultFileName}({index})'
        exists = check()
        index += 1

    # set path with new name
    newPath = join(newFileName)

    # open file and show new path
    newFile = open(newPath, 'a')
    path = newPath
    app.path_label.configure(text=f'Current path: {path}')

    # confirm to user
    def reset_confirm():
        app.confirm_label.configure(text='')
    app.confirm_label.configure(text=f'created {newFileName}', text_color='green')
    app.after(2000, reset_confirm)


# get file path from user
def getPath():
    global path
    try:
        new_path = filedialog.askopenfilename(
            title="Select a File",
            filetypes=(("Text Files", "*.txt"), ("All Files", "*.*"))
        )
        if new_path:
            path = new_path
    except Exception as e:
        msg.showerror("Unexpected Error!", f"error occured {e}")
    finally:
        if '.txt' not in path:
            msg.showerror('Error!', 'Please select a .txt file')
            path = None
        app.path_label.configure(text=f'Current path: {path}')
        return path

    
# actually does the saving
def actuallyLog():
    global path, C1La, C1Lo, C2La, C2Lo, Dis, verticalResult, timestamp

    def revert_confirmation():
        app.confirm_label.configure(text='')

    # show logging
    app.confirm_label.configure(text='Logging...', text_color='yellow')

    # log to file
    timestamp = dt.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    with open(path, 'a') as file:
        file.write(f'calculated at {timestamp} \n')
        file.write(f'first coordinates: ({C1La},{C1Lo}) \n')
        file.write(f'second coordinates: ({C2La},{C2Lo}) \n')
        file.write(f'distance between points: {Dis}u \n')
        file.write(f'\n')
        file.write(f'{verticalResult} \n')
        file.write(f'-' * 40 + '\n')

    # confirm to user
    app.confirm_label.configure(text='Done!', text_color='green')
    app.after(1500, revert_confirmation)


# sees wether it needs to get the path first
def logResults():
    global path, calcDone
    if calcDone:
        if path is not None and '.txt' in path:
            actuallyLog()
        else:
            path = getPath()
            if path is not None and '.txt' in path:
                actuallyLog()
            elif path is not None:
                # show error message and confirmation on app
                app.confirm_label.configure(text='Failed to save', text_color='red')
                
                msg.showerror("Log Error!", f"Could not save to {path}")

                def reset_confirmation():
                    app.confirm_label.configure(text='')
                
                app.after(2000, reset_confirmation)

                #reset path for next time
                path = None

def openFile():
    global path
    if path is not None:
        try:
            if os.path.exists(path):
                if sys.platform in ('win32', 'cygwin', 'msys'):  # windows
                    os.startfile(path)
                elif sys.platform == "darwin":  # macOS
                    subprocess.run(["open", path])
                else:  # Linux
                    subprocess.run(["xdg-open", path])
            else:
                msg.showerror(f'Error!', f'''Could not open {path} 
Perhaps it was deleted or renamed''')
        except Exception as e:
            msg.showerror(f'Error!', f'{e}')





# main layout
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # setup
        ico_path=resource_path('Icons/icon.ico')
        icns_path=resource_path('Icons/icon.icns')
        self.title('')
        self.resizable(False,False)

        try:
            if sys.platform == 'darwin':   # check for mac
                from AppKit import NSApplication, NSImage

                ns_app = NSApplication.sharedApplication()
                ns_icon = NSImage.alloc().initWithContentsOfFile_(icns_path)
                ns_app.setApplicationIconImage_(ns_icon)
            elif sys.platform in ('win32', 'cygwin', 'msys'):  # check for windows
                self.iconbitmap(ico_path)
                self.icon=ico_path
        except:
            pass

        # set dark mode based on text file
        try:
            mode_path=writable_path('mode.txt')
            with open(mode_path, "r") as file:
                content = file.read()
                ctk.set_appearance_mode(content)
                if content == 'dark':
                    lightMode = False
                elif content == 'light':
                    lightMode = True
                self.lightModeForMenu = tk.BooleanVar(value=lightMode)
        except:
            msg.showerror('Error!', f'Could not open {mode_path}')
        
        # title
        self.title_label=ctk.CTkLabel(self, text='No Man\'s Sky Layline Finder', font=(nms,25), height=50, fg_color=('#FF6865','black'), text_color=('black','red'), corner_radius=10)
        self.title_label.grid(row=0,column=0, padx=10,pady=10, columnspan=2, sticky='ew')

        # make the input frame
        self.inputs_frame=inputFrame(self)
        self.inputs_frame.grid(row=1,column=0, padx=20,pady=5, columnspan=2, sticky='sew')

        # bottom row of buttons
        try:   # just in case image file is missing or in the wront spot
            run_path = resource_path('Images/run.png')
            self.icon=ctk.CTkImage(light_image=Image.open(run_path), dark_image=Image.open(run_path), size=(16,16))
            self.run_button=ctk.CTkButton(self, text='Locate', font=(nms,16), width=250, corner_radius=12, image=self.icon, command=self.give_inputs)
        except:
            self.run_button=ctk.CTkButton(self, text='Locate', font=(nms,16), width=300, corner_radius=10, command=self.give_inputs)
        self.clear_button=ctk.CTkButton(self, text='Clear', font=(nms,14), width=45, fg_color='transparent',border_width=2,border_color='red',text_color='red',hover_color=('#FFB3B2','dark red'), command=self.clearInputs)
        #
        self.run_button.grid(row=2,column=0, padx=10,pady=10, sticky='ew')
        self.clear_button.grid(row=2,column=1, padx=10,pady=10, sticky='w')

       
       
        # results screen
        self.results_title=ctk.CTkLabel(self, text='Laylines at these longitudes:', font=(nms,18))
        self.confirm_label=ctk.CTkLabel(self, text='', font=(nms,18))
        self.results_frame=resultsFrame(self)
        #
        try:
            back_path = resource_path('Images/back.png')
            self.back_icon=ctk.CTkImage(light_image=Image.open(back_path), dark_image=Image.open(back_path), size=(20,20))
            self.back_button=ctk.CTkButton(self, text='',image=self.back_icon, width=20, corner_radius=10, font=(nms,15), command=self.back)
        except:
            self.back_button=ctk.CTkButton(self, text='', width=20, corner_radius=10, font=(nms,15), command=self.back)
        self.log_button=ctk.CTkButton(self, text='Log Results', font=(nms,15), command=logResults)
        self.path_button=ctk.CTkButton(self, text='Change Path', font=(nms,15), command=getPath)
        self.open_button=ctk.CTkButton(self, text='Open File', font=(nms,15), command=openFile)
        self.new_file_button=ctk.CTkButton(self, text='New File', font=(nms,15), command=makeNew)
        self.path_label=ctk.CTkLabel(self, text=f'Current path: {path}', font=(nms,13))

        # guide screen
        self.guide_title=ctk.CTkLabel(self, text='How To Use the Calculator', font=(nms,22))
        try:
            guide_path=resource_path('Text/guide.txt')
            guide_file=open(guide_path,'r')
            guide_text=guide_file.read()
            guide_file.close()
            self.guide_label=ctk.CTkLabel(self, text=guide_text, justify='left')
            guide_file.close()
        except:
            self.guide_label=ctk.CTkLabel(self, text='<MISSING TEXT FILE>')
        try:
            video_path=resource_path('Images/video.png')
            self.video_icon=ctk.CTkImage(light_image=Image.open(video_path), dark_image=Image.open(video_path), size=(20,20))
            self.video_button=ctk.CTkButton(self, text='Video Guide', image=self.video_icon, command=lambda: web.open_new_tab('https://youtu.be/Ec8QN39GNB8'))
        except:
            self.video_button=ctk.CTkButton(self, text='Video Guide', command=lambda: web.open_new_tab('https://youtu.be/Ec8QN39GNB8'))

        # info screen
        self.info_title_deposits=ctk.CTkLabel(self, text='3-Star Deposits', font=(nms,22))
        self.info_title_laylines=ctk.CTkLabel(self, text='Laylines', font=(nms,22))
        self.info_deposits_frame=infoFrameDeposits(self)
        self.info_laylines_frame=infoFrameLaylines(self)


        # about screen
        self.about_title=ctk.CTkLabel(self, text='About', font=(nms,22))
        #
        try:
            about_path=resource_path('Text/about.txt')
            about_file=open(about_path, 'r')
            about_text=about_file.read()
            about_file.close()
            self.about_label=ctk.CTkLabel(self, text=about_text, justify='left')
            about_file.close()
        except:
            self.about_label=ctk.CTkLabel(self, text='<MISSING TEXT FILE>')
        #
        try:
            mail_path = resource_path('Images/mail.png')
            self.mail_icon=ctk.CTkImage(light_image=Image.open(mail_path), dark_image=Image.open(mail_path), size=(20,20))
            self.about_email_button=ctk.CTkButton(self, text='Contact Me', image=self.mail_icon, command=lambda: web.open_new_tab('https://mail.google.com/mail/?view=cm&fs=1&to=soupcat.py@gmail.com'))
        except:
            self.about_email_button=ctk.CTkButton(self, text='Contact Me', command=lambda: web.open_new_tab('https://mail.google.com/mail/?view=cm&fs=1&to=soupcat.py@gmail.com'))
        #
        try:
            code_path = resource_path('Images/code.png')
            self.code_icon=ctk.CTkImage(light_image=Image.open(code_path), dark_image=Image.open(code_path), size=(24,20))
            self.about_code_button=ctk.CTkButton(self, text='View Code', image=self.code_icon, command=lambda: web.open_new_tab('https://github.com/SoupCat-Py/NMS-Layline-Calculator/blob/main/NMSLC-v3.py'))
        except:
            self.about_code_button=ctk.CTkButton(self, text='View Code', command=lambda: web.open_new_tab('https://github.com/SoupCat-Py/NMS-Layline-Calculator/blob/main/NMSLC-v3.py'))

        # make keybinds
        self.bind_all('<Return>', lambda event: self.give_inputs())
        #
        self.bind_all('<Control-s>', lambda event: logResults())
        self.bind_all('<Control-p>', lambda event: getPath())
        self.bind_all('<Control-o>', lambda event: openFile())
        self.bind_all('<Control-n>', lambda event: makeNew())
        self.bind_all('<Control-q>', lambda event: self.quit())
        self.bind_all('<Control-c>', lambda event: self.clearInputs())
        self.bind_all('<Escape>', lambda event: self.back())


        # make menu bar
        self.create_menu_bar()



    # define hiding of layout
    def hideLayout(self):
        global main
        self.inputs_frame.grid_forget()
        self.run_button.grid_forget()
        self.clear_button.grid_forget()
        self.log_button.grid_forget()
        self.path_button.grid_forget()
        self.open_button.grid_forget()
        self.new_file_button.grid_forget()
        self.path_label.grid_forget()
        #
        self.results_title.grid_forget()
        self.confirm_label.grid_forget()
        self.results_frame.grid_forget()
        #
        self.guide_title.grid_forget()
        self.guide_label.grid_forget()
        self.video_button.grid_forget()
        #
        self.info_title_deposits.grid_forget()
        self.info_title_laylines.grid_forget()
        self.info_deposits_frame.grid_forget()
        self.info_laylines_frame.grid_forget()
        #
        self.about_title.grid_forget()
        self.about_label.grid_forget()
        self.about_email_button.grid_forget()
        self.about_code_button.grid_forget()

        self.back_button.grid_forget()
        main = False

    # define back button function
    def back(self):
        global main
        if not main:
            self.hideLayout()

            # show main screen
            self.inputs_frame.grid(row=1,column=0, padx=20,pady=5, columnspan=2, sticky='sew')
            self.run_button.grid(row=2,column=0, padx=10,pady=10, sticky='ew')
            self.clear_button.grid(row=2,column=1, padx=10,pady=10, sticky='w')

            # tell the script the main screen on
            main = True

    # method for menu bar
    def create_menu_bar(self):

        # create the menu bar
        menu_bar=tk.Menu(self)
        self.config(menu=menu_bar)

        # add file menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
            # commands
        file_menu.add_command(label='save (ctrl-s)', command=logResults)
        file_menu.add_command(label='change path (ctrl-p)', command=getPath)
        file_menu.add_command(label='open file (ctrl-o)', command=openFile)
        file_menu.add_command(label='new txt file (ctrl-n)', command=makeNew)
        file_menu.add_separator()
        file_menu.add_command(label='quit (ctrl-q)', command=self.quit)
            # add to menu bar
        menu_bar.add_cascade(label='File', menu=file_menu)

        # add view menu
        view_menu=tk.Menu(menu_bar, tearoff=0)
        view_menu.add_checkbutton(label='light mode', variable=self.lightModeForMenu, command=self.toggle_dark_mode)
        menu_bar.add_cascade(label='View', menu=view_menu)

        # add help menu
        help_menu=tk.Menu(menu_bar, tearoff=0)
            # commands
        help_menu.add_command(label='info', command=self.show_info)
        help_menu.add_command(label='guide', command=self.show_guide)
        help_menu.add_command(label='about', command=self.show_about)
            # add to menu bar
        menu_bar.add_cascade(label='Help', menu=help_menu)

        # add run menu
        run_menu=tk.Menu(menu_bar, tearoff=0)
        run_menu.add_command(label='calculate (enter)', command=self.give_inputs)
        menu_bar.add_cascade(label='Run', menu=run_menu)



    def open_popup(self):
        popup_window=ctk.CTkToplevel(self)
        popup_window.title('Error!')

        self.error_text=ctk.CTkLabel(popup_window, text='''Please check that no input fields are blank 
before running the calculation''', font=('Helvetica', 16))
        self.close_button=ctk.CTkButton(popup_window, text='Got it', corner_radius=10, fg_color='red',hover_color='dark red', command=popup_window.destroy)

        self.error_text.grid(row=0,column=0, padx=10,pady=10, sticky='nsew')
        self.close_button.grid(row=1,column=0, padx=10,pady=10, sticky='ew')

    # calculate button command
    def give_inputs(self):
        global C1La, C1Lo, C2La, C2Lo, Dis
        # assign variables to inputs
        try:
            C1La=float(self.inputs_frame.c1_input_lat.get())
            C1Lo=float(self.inputs_frame.c1_input_long.get())
            C2La=float(self.inputs_frame.c2_input_lat.get())
            C2Lo=float(self.inputs_frame.c2_input_long.get())
            Dis=float(self.inputs_frame.d_input.get())

            if Dis > 0:
                # call calculate function
                self.results_list=calculate(C1La, C2La, C1Lo, C2Lo, Dis)
                # show results to the user
                self.hideLayout()
                    # show results widgets
                self.results_title.grid(row=1,column=1, padx=10,pady=3, sticky='ew')
                self.confirm_label.grid(row=1,column=0, sticky='ew')
                self.results_frame.grid(row=2,column=1, padx=10,pady=10, rowspan=5, sticky='ew', columnspan=2)
                self.back_button.grid(row=2,column=0, padx=10,pady=10, sticky='e')
                self.log_button.grid(row=3,column=0, padx=10,pady=5, sticky='e')
                self.path_button.grid(row=4,column=0, padx=10,pady=5, sticky='e')
                self.open_button.grid(row=5,column=0, padx=10,pady=5, sticky='e')
                self.new_file_button.grid(row=6,column=0, padx=10,pady=5, sticky='e')
                self.path_label.grid(row=7,column=0, padx=5,pady=5, columnspan=2, sticky='ew')
                    # update label in frame
                self.results_frame.results_label.configure(text=self.results_list)
        except:
            self.open_popup()

        


    # clear button command
    def clearInputs(self):
        self.inputs_frame.c1_input_lat.delete(0, ctk.END)
        self.inputs_frame.c2_input_lat.delete(0, ctk.END)
        self.inputs_frame.c1_input_long.delete(0, ctk.END)
        self.inputs_frame.c2_input_long.delete(0, ctk.END)
        self.inputs_frame.d_input.delete(0, ctk.END)


    # file menu commands
    def quit(App):
        App.destroy()
        os._exit(0)

    # view menu commands
    def toggle_dark_mode(self):
        mode_path=writable_path('mode.txt')
        with open(mode_path, "r") as file:
            content = file.read()

        if 'dark' in content:
            ctk.set_appearance_mode('light')

            # change setting in file
            with open(mode_path, "w") as file:
                file.write(content.replace('dark', 'light'))

        elif 'light' in content:
            ctk.set_appearance_mode('dark')

            # change setting in file
            with open(mode_path, 'w') as file:
                file.write(content.replace('light', 'dark'))

    # help menu commands
    def show_guide(self):
        self.hideLayout()
        self.guide_title.grid(row=1,column=0, padx=10,pady=10, columnspan=2)
        self.guide_label.grid(row=2,column=0, padx=15,pady=10, columnspan=2)
        self.video_button.grid(row=3,column=1, padx=20,pady=10, sticky='ew')
        self.back_button.grid(row=3,column=0, padx=10,pady=10, sticky='w')
    def show_info(self):
        self.hideLayout()
        self.info_title_deposits.grid(row=1,column=0, padx=10,pady=10)
        self.info_title_laylines.grid(row=1,column=1, padx=10,pady=10)
        self.info_deposits_frame.grid(row=2,column=0, padx=10,pady=10, sticky='ns')
        self.info_laylines_frame.grid(row=2,column=1, padx=10,pady=10, sticky='ns')
        self.back_button.grid(row=3,column=0, padx=10,pady=10, sticky='w')
    def show_about(self):
        self.hideLayout()
        self.title_label.grid(row=0,column=0, columnspan=3)
        self.about_title.grid(row=1,column=0, padx=10,pady=10, columnspan=3)
        self.about_label.grid(row=2,column=0, padx=15,pady=10, columnspan=3)
        self.back_button.grid(row=3,column=0, padx=10,pady=10, sticky='w')
        self.about_email_button.grid(row=3,column=1, padx=10,pady=10)
        self.about_code_button.grid(row=3,column=2, padx=10,pady=10)


# define the frame for user inputs
class inputFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)

        def validate_decimal_input(input):
            if input == '' or input == '-' or input in ('lat','long','distance'): # allow empty input, negative, and placeholder
                return True
            try: # try converting to a float
                float(input)
                return True
            except:
                return False

        # labels
        self.c1_label=ctk.CTkLabel(self, text='First Coordinates:', font=(nms,18))
        self.c2_label=ctk.CTkLabel(self, text='Second Coordinates:', font=(nms,18))
        self.d_label=ctk.CTkLabel(self, text='Distance:', font=(nms,18))
        #
        self.c1_label.grid(row=0,column=0, padx=10,pady=10, sticky='e')
        self.c2_label.grid(row=1,column=0, padx=10,pady=10, sticky='e')
        self.d_label.grid(row=2,column=0, padx=10,pady=10, sticky='e')

        # inputs
        validate_command=self.register(validate_decimal_input)
        self.c1_input_lat=ctk.CTkEntry(self, placeholder_text='lat', width=60, font=(nms,14), validate='key', validatecommand=(validate_command, '%P'))
        self.c1_input_long=ctk.CTkEntry(self, placeholder_text='long', width=60, font=(nms,14), validate='key', validatecommand=(validate_command, '%P'))
        self.c2_input_lat=ctk.CTkEntry(self, placeholder_text='lat', width=60, font=(nms,14), validate='key', validatecommand=(validate_command, '%P'))
        self.c2_input_long=ctk.CTkEntry(self, placeholder_text='long', width=60, font=(nms,14), validate='key', validatecommand=(validate_command, '%P'))
        self.d_input=ctk.CTkEntry(self, placeholder_text='distance', width=120, font=(nms,14), validate='key', validatecommand=(validate_command, '%P'))
        #
        self.c1_input_lat.grid(row=0,column=1, padx=5,pady=10, sticky='ew')
        self.c1_input_long.grid(row=0,column=2, padx=5,pady=10, sticky='ew')
        self.c2_input_lat.grid(row=1,column=1, padx=5,pady=10, sticky='ew')
        self.c2_input_long.grid(row=1,column=2, padx=5,pady=10, sticky='ew')
        self.d_input.grid(row=2,column=1, padx=5, pady=10, sticky='ew', columnspan=2)

        

# define results frame
class resultsFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.results_label=ctk.CTkLabel(self, text='<PLACEHOLDER>', font=('Helvetica',18), anchor='center',justify='center')
        self.results_label.pack(expand=True, padx=10,pady=10)

# define info screen frames
class infoFrameDeposits(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        try:
            info_deposits_path = resource_path('Text/info_deposits.txt')
            info_deposits_file = open(info_deposits_path, 'r')
            info_deposits_text = info_deposits_file.read()
            info_deposits_file.close()
            self.info_deposits_label=ctk.CTkLabel(self, text=info_deposits_text, justify='left')
            info_deposits_file.close()
        except:
            self.info_deposits_label=ctk.CTkLabel(self, text='<MISSING TEXT FILE>', justify='left')
        self.info_deposits_label.grid(row=0,column=0, padx=10,pady=10)
class infoFrameLaylines(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        try:
            info_laylines_path = resource_path('Text/info_laylines.txt')
            info_laylines_file = open(info_laylines_path, 'r')
            info_laylines_text = info_laylines_file.read()
            info_laylines_file.close()
            self.info_laylines_label=ctk.CTkLabel(self, text=info_laylines_text, justify='left')
            info_laylines_file.close()
        except:
            self.info_laylines_label=ctk.CTkLabel(self, text='<MISSING TEXT FILE>', justify='left')
        self.info_laylines_label.grid(row=0,column=0, padx=10,pady=10)



if __name__ == '__main__':
    try:
        app=App()
        app.mainloop()
    except Exception as e:  # if the program crashes or an error occures
        import traceback
        # get error log file
        crash_path = writable_path('crash_log.txt')
        # write error details
        with open (crash_path, 'a') as log:
            log.write(f'error occured at {dt.datetime.now()}:\n')
            log.write(traceback.format_exc())
            log.write('\n\n')
        # display error message
        msg.showerror("Unexpected Error", "The application encountered an error and needs to close.")
os._exit(0)

import os
import stat
import time
import datetime


def main():
    """
    Main function to allow the user to pick which naming scheme they want
    TODO: Bring everything up to standards
    - Rename script name to screenshots_renamer.py
    - Implement steam side of improvements
    - Implement 'preview' like in screenshots organiser?
    """
    
    # we dedicate this block for debugging :)
    debug = True
    if debug:
        test_folder = "test_screenshots" # <--- change here
        script_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), test_folder)
    else:
        # set cwd to location of the script
        script_directory = os.path.dirname(os.path.abspath(__file__))
    
    os.chdir(script_directory) 

    # Warnings
    print("-----------------------!! WARNING !!---------------------------"
          "\nThis script will rename image files in the current folder!"
          "\nThere is no undo function available."
          "\n-----------------------!! WARNING !!---------------------------"
          "\nAre you sure you want to proceed? Type y/n: ")

    usr = str(input()).lower()
    if usr == 'y' or usr == 'yes':
        # Pick screenshot renaming scheme
        print("-----------------------"
              "\nSelect naming scheme..."
              "\n-----------------------"
              "\n1: Windows "
              "\n   e.g 2020-01-29 (8)"
              "\n2: Steam "
              "\n   e.g 1172470_20200129203829_8")
        scheme = input("Please enter the number of the naming scheme to be used: ").strip()
        if scheme == "1":
            # get mapping
            mapping = get_files_to_rename(script_directory)
            # renaming
            output_csv_filename = 'screenshots_renamer_results.csv'
            output_csv_filepath = os.path.join(script_directory, output_csv_filename)
            rename_files(mapping, output_csv_filepath, False)
            ExitMethods.finished()
        elif scheme == "2":
            rename_steam()
            ExitMethods.finished()
        else:
            ExitMethods.invalid()

    elif usr == 'n' or usr == 'no':
        ExitMethods.normal_exit()
    else:
        ExitMethods.invalid()


def get_files_to_rename(directory_path:str, naming_scheme:str, steam_app_id:str=None) -> dict:
    """
    For all files in the directory, generate a mapping between old files and new files
    - Decide whether a file should be renamed or not (e.g rename if .png)
    - Handles edge case where multiple old files was going to map to the same new file

    :param directory_path: the absolute path to the directory containing files to rename
    :param naming_scheme: one of ['Windows', 'Steam'] - case insensitive
    :param steam_app_id: if 'Steam' is chosen, then it uses the app id as prefix for the new name, defaults to None
    :return: a mapping dictionary, where {old filepath: new filepath}
    """

    # for each file in current folder, if applicable, propose a new filename (based on scheme) --> create a mapping dict. out of this?
    files_to_rename = {} # old_filepath: new_filepath
    for file in os.listdir(directory_path):

        # get file extension
        try:
            file_extension = os.path.splitext(file)[1] # e.g .png - note the '.' is included
        except IndexError as error:
            msg = f"Index error when getting file extension for file: {file}. If file has no extension, ignore this message."
            print(msg)

        if file_extension in StandardVariables.accepted_extensions:
            # extract the most recent modification date for the file, then format as string according to formatting rules
            filepath = os.path.join(directory_path, file)
            modified_timestamp = os.stat(filepath)[stat.ST_MTIME]
            modified_datetime = datetime.datetime.fromtimestamp(modified_timestamp)

            if naming_scheme.lower() == "windows":

                modified_datetime_formatted = modified_datetime.strftime(StandardVariables.windows_datetime_formatting)  # e.g '2020-01-29'
                        
                # propose new filename and add duplicate suffix if appropriate
                proposed_filename = f"{modified_datetime_formatted}{file_extension}"
                proposed_filepath = os.path.join(directory_path, proposed_filename)

                # handle edge case of renaming multiple old files to the same proposed filename
                # - extra logic: if in files_to_skip, it will exist so we need to take that into account too
                # - windows duplicate example: file.png -> file (1).png -> file (2).png -> ...
                duplicate_index = 0
                duplicate_exists = os.path.isfile(proposed_filepath) or proposed_filepath in files_to_rename.values()
                while duplicate_exists:
                    duplicate_index += 1
                    proposed_filename = f"{modified_datetime_formatted} ({duplicate_index}){file_extension}"  # e.g '2020-01-29 (1).png'
                    proposed_filepath = os.path.join(directory_path, proposed_filename)
                    duplicate_exists = os.path.isfile(proposed_filepath) or proposed_filepath in files_to_rename.values()

                # record mapping between old filepath and proposed filepath
                files_to_rename[filepath] = proposed_filepath

            elif naming_scheme.lower() == "steam":

                modified_datetime_formatted = modified_datetime.strftime(StandardVariables.steam_datetime_formatting)  # e.g '20200129203829'

                # propose new filename and add duplicate suffix if appropriate
                proposed_filename = f"{steam_app_id}_{modified_datetime_formatted}{file_extension}"
                proposed_filepath = os.path.join(directory_path, proposed_filename)

                # handle edge case of renaming multiple old files to the same proposed filename
                # - extra logic: if in files_to_skip, it will exist so we need to take that into account too
                # - steam duplicate example: file_1.png -> file_2.png -> file_3.png -> ...
                duplicate_index = 1
                duplicate_exists = os.path.isfile(proposed_filepath) or proposed_filepath in files_to_rename.values()
                while duplicate_exists:
                    duplicate_index += 1
                    proposed_filename = f"{steam_app_id}_{modified_datetime_formatted}_{duplicate_index}{file_extension}"  # e.g '1237970_20200129203829_2.png'
                    proposed_filepath = os.path.join(directory_path, proposed_filename)
                    duplicate_exists = os.path.isfile(proposed_filepath) or proposed_filepath in files_to_rename.values()

                # record mapping between old filepath and proposed filepath
                files_to_rename[filepath] = proposed_filepath

    return files_to_rename


def rename_files(file_rename_mapping:dict, results_csv_path:str, dry_run:bool=True):
    """
    Rename files according to a mapping dictionary where {old filepath: new filepath}.
    Has a dry run functionality that prints instead of renames.

    :param file_rename_mapping: a mapping dictionary, where {old filepath: new filepath} - i.e the output of get_files_to_rename()
    :param results_directory_path: path to where the output results (.csv) will be saved - this will overwrite the file if already exists
    :param dry_run: print the files to rename if True; rename the files if False, defaults to True
    """
    
    rename_results = ['old file name, new (proposed) file name, status\n'] # header for output csv
    for filepath, proposed_filepath in file_rename_mapping.items():
        status = ""
        if dry_run:
            print(f"(Dry run) | {os.path.basename(filepath):20} ------> {os.path.basename(proposed_filepath):20}")
            status = "N/A (dry run)"
        else:
            try:
                os.rename(filepath, proposed_filepath)
                print(f"{os.path.basename(filepath):20} ------> {os.path.basename(proposed_filepath):20}")
                status = "success"
            except FileExistsError:
                print("ERROR: Cannot rename", filepath, "to", proposed_filepath + "! File already exists.")
                status = "failed"
                
        rename_results.append(f"{filepath}, {proposed_filepath}, {status}\n")

    # save results to csv
    with open(results_csv_path, 'w') as csv:
        csv.writelines(rename_results)
        print(f"Saved log to {results_csv_path}")


def rename_steam():
    """
        This naming scheme loops through the current folder and looks for image files, then
        renames them according to most recent date of modification without duplicates.

        Format is AppID_YYYYMMDDHHMMSS_N.extension

        Note: Time of most recent content modification is more reliable than day of creation
        Note2: Only recognises jpg and png (most common extensions) at the moment
        """

    print("----------------------------------"
          "\nRenaming using the Steam scheme!"
          "\n----------------------------------")

    app_id = str(input("Please enter the AppID: "))
    while not app_id.isdigit():
        app_id = str(input("AppID must be an integer! Please enter the AppID: "))

    # Setting up: extensions and dictionary for month conversion (e.g Jun -> 06)
    accepted_extensions = StandardVariables.accepted_extensions
    month_dict = StandardVariables.months

    # (ARGH IT'S SO BAD) Loop through current directory and find files with already-correct naming scheme
    already_correct = find_existing_steam(app_id)

    # Get current directory, then loop through its files to find which ones are screenshots
    current_directory = os.curdir

    for file in os.listdir(current_directory):
        file_extension = file[-4:]
        if (file not in already_correct) and (file_extension in accepted_extensions):
            # Extract date of most recent content modification
            filepath = os.path.join(os.curdir, file)
            filestatobject = os.stat(filepath)

            # Extract most recent modification date and split into variables
            # Note: ctime() returns a string from the datetime object
            modified_datetime = time.ctime(filestatobject[stat.ST_MTIME]).split()  # e.g [Mon, Jul, 8, 01:16:44, 2019]
            modified_time = modified_datetime[3].replace(":", "")
            modified_day = "{:02d}".format(int(modified_datetime[2]))
            modified_month = month_dict.get(str(modified_datetime[1]))
            modified_year = str(modified_datetime[-1])
            duplicate_index = 1

            # Propose a possible filename and add duplicate index if appropriate
            # e.g 1172470_20200129203829_1
            proposed_filename = app_id + '_' + modified_year + modified_month + \
                                modified_day + modified_time + '_' + \
                                str(duplicate_index) + file_extension
            duplicate_exist = os.path.isfile(proposed_filename)  # T if dupe exists, F otherwise
            while duplicate_exist:
                duplicate_index += 1
                proposed_filename = app_id + '_' + modified_year + \
                                    modified_month + modified_day + modified_time + '_' + \
                                    str(duplicate_index) + file_extension
                duplicate_exist = os.path.isfile(proposed_filename)

            # Rename the file to proposed filename
            try:
                os.rename(filepath, proposed_filename)
            except FileExistsError:
                print("ERROR: Cannot rename", filepath, "to", proposed_filename + "! File already exists.")


def find_existing_steam(app_id):
    """
    Modified version of the rename_steam function, used to find which pictures in the folder
    already has correct naming.

    Differences in code will be highlighted by comments in CAPITAL LETTERS.

    Output: a Python set containing filenames with already-correct naming scheme
    """

    # Known filenames will go here
    already_correct = set()

    # Setting up: extensions and dictionary for month conversion (e.g Jun -> 06)
    accepted_extensions = StandardVariables.accepted_extensions
    month_dict = StandardVariables.months

    # Get current directory, then loop through its files to find which ones are screenshots
    current_directory = os.curdir
    for file in os.listdir(current_directory):
        file_extension = file[-4:]
        if file_extension in accepted_extensions:
            # If file is a picture, extract date of most recent content modification
            filepath = os.path.join(os.curdir, file)
            filestatobject = os.stat(filepath)

            # Extract most recent modification date and split into variables
            # Note: ctime() returns a string from the datetime object
            modified_datetime = time.ctime(filestatobject[stat.ST_MTIME]).split()  # e.g [Mon, Jul, 8, 01:16:44, 2019]
            modified_time = modified_datetime[3].replace(":", "")
            modified_day = "{:02d}".format(int(modified_datetime[2]))
            modified_month = month_dict.get(str(modified_datetime[1]))
            modified_year = str(modified_datetime[-1])
            duplicate_index = 1

            # Propose a possible filename and add duplicate index if appropriate
            # e.g 1172470_20200129203829_1
            proposed_filename = app_id + '_' + modified_year + modified_month + \
                                modified_day + modified_time + '_' + \
                                str(duplicate_index) + file_extension
            duplicate_exist = os.path.isfile(proposed_filename)  # T if dupe exists, F otherwise
            while duplicate_exist:
                already_correct.add(proposed_filename)  # ADD TO SET OF KNOWN CORRECT FILENAMES
                duplicate_index += 1
                proposed_filename = app_id + '_' + modified_year + modified_month + \
                                    modified_day + modified_time + '_' + \
                                    str(duplicate_index) + file_extension
                duplicate_exist = os.path.isfile(proposed_filename)

            # REMOVED RENAMING TRY/EXCEPT

    return already_correct  # RETURN SET


class StandardVariables:
    """ Class that defines the standards for frequently-used variables, such as a list of accepted extensions
    """

    accepted_extensions = [".jpg", ".png", ".bmp"]
    months = {
        "Jan": "01",
        "Feb": "02",
        "Mar": "03",
        "Apr": "04",
        "May": "05",
        "Jun": "06",
        "Jul": "07",
        "Aug": "08",
        "Sep": "09",
        "Oct": "10",
        "Nov": "11",
        "Dec": "12",
    }
    windows_datetime_formatting = "%Y-%m-%d" # e.g 2020-01-29
    steam_datetime_formatting = "%Y%m%d%H%M%S" # e.g 20200129203829


class ExitMethods:
    @staticmethod
    def finished():
        input("Finished! Press ENTER to exit...")
        exit()

    @staticmethod
    def normal_exit():
        input("Press ENTER to exit...")
        exit()

    @staticmethod
    def invalid():
        input("Invalid response!"
              "\nPress ENTER to exit...")
        exit()


if __name__ == "__main__":

    main()

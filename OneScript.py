#!/usr/bin/env python
# 0.0.34
import os, subprocess, shlex, datetime, sys, json, ssl, argparse, re

# Python-aware urllib stuff
if 2/3!=0:
    from urllib.request import urlopen
else:
    # Import urllib2 to catch errors
    import urllib2
    from urllib2 import urlopen
    input = raw_input

skip_repos = (
    "OneScript",
    "Hackintosh-Guide",
    "Hackintosh-Tips-And-Tricks",
    "CorpBot-Docker",
    "camielbot",
    "OpenCorePkg",
    "AMD_Vanilla"
)
per_page = 100 # 100 is the max
repo_url = "https://api.github.com/users/corpnewt/repos?per_page={}".format(per_page)
base_url = "https://raw.githubusercontent.com/corpnewt/OneScript/master/{}"
file_list = ("OneScript.py","OneScript.command","OneScript.bat")

def run_command(comm, shell = False):
    c = None
    try:
        if shell and type(comm) is list:
            comm = " ".join(shlex.quote(x) for x in comm)
        if not shell and type(comm) is str:
            comm = shlex.split(comm)
        p = subprocess.Popen(comm, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        c = p.communicate()
        return (c[0].decode("utf-8", "ignore"), c[1].decode("utf-8", "ignore"), p.returncode)
    except:
        if not c: return ("", "Command not found!", 1)
        return (c[0].decode("utf-8", "ignore"), c[1].decode("utf-8", "ignore"), p.returncode)

def open_url(url):
    # Wrap up the try/except block so we don't have to do this for each function
    try:
        response = urlopen(url)
    except Exception as e:
        if 2/3!=0 or not (isinstance(e, urllib2.URLError) and "CERTIFICATE_VERIFY_FAILED" in str(e)):
            # Either py3, or not the right error for this "fix"
            return None
        # Py2 and a Cert verify error - let's set the unverified context
        context = ssl._create_unverified_context()
        try:
            response = urlopen(url, context=context)
        except:
            # No fixing this - bail
            return None
    return response

def _get_string(url):
    response = open_url(url)
    if not response:
        return None
    CHUNK = 16 * 1024
    bytes_so_far = 0
    try: total_size = int(response.headers['Content-Length'])
    except: total_size = -1
    chunk_so_far = "".encode("utf-8")
    while True:
        chunk = response.read(CHUNK)
        bytes_so_far += len(chunk)
        if not chunk: break
        chunk_so_far += chunk
    return chunk_so_far.decode("utf-8")

def get_version(text):
    try: return text.split("\n")[1][2:]
    except: return "Unknown"

def check_update():
    target_dir = os.path.dirname(os.path.realpath(__file__))
    # Checks against https://raw.githubusercontent.com/corpnewt/OneScript/master/OneScript.command to see if we need to update
    print("Checking for Updates...")
    with open(os.path.realpath(__file__), "r") as f:
        # Our version should always be the second line
        version = get_version(f.read())
    print(" - Current version: {}".format(version))
    try:
        new_py = _get_string(base_url.format(file_list[0]))
        new_version = get_version(new_py)
        print(" - Remote version:  {}".format(new_version))
    except Exception as e:
        # Not valid json data
        print("Error checking for updates:\n{}".format(e))
        return
    print("")
    if new_version.lower() == "unknown" or version == new_version:
        # Greater, or the same - return
        print("No update needed.")
        return True
    # Let's pad the version numbers to the same length
    # and do the same for the number of chars in each sub version
    v = version.split(".")
    nv = new_version.split(".")
    v_len = len(max((v,nv),key=len))
    pad   = len(max(v+nv,key=len))
    v = ".".join([x.rjust(pad,"0") for x in v] + ["0".rjust(pad,"0") for x in range(v_len-len(v))])
    nv = ".".join([x.rjust(pad,"0") for x in nv] + ["0".rjust(pad,"0") for x in range(v_len-len(nv))])
    # No need to update
    if v >= nv:
        print("No update needed.")
        return True
    print("Needs update - gathering files...")
    if os.path.basename(__file__) != file_list[0]:
        print(" - Source files renamed - adjusting...")
        file_name = ".".join(os.path.basename(__file__).split(".")[:-1])
        adjusted = [file_name+"."+x.split(".")[-1] for x in file_list]
        adjusted = []
        for x in file_list:
            new_name = file_name+"."+x.split(".")[-1]
            print(" --> {} -> {}".format(x,new_name))
            adjusted.append(new_name)
    else:
        adjusted = [x for x in file_list]
    try:
        # Update each file
        for i,f in enumerate(adjusted):
            fp = os.path.join(target_dir,f)
            print(" - Checking {}...".format(f))
            if not os.path.exists(fp):
                print(" --> Skipped (not found locally)...")
                continue # Don't update files we don't have
            print(" --> Downloading...")
            file_contents = _get_string(base_url.format(file_list[i]))
            print(" --> Replacing...")
            with open(fp, "w") as x:
                x.write(file_contents)
            # chmod +x on non-Windows, then restart
            if os.name!="nt" and not f.lower().endswith(".bat"):
                print(" --> Setting executable mode...")
                run_command(["chmod", "+x", fp])
    except Exception as e:
        print("Error gathering files:\n{}".format(e))
        return
    print("")
    print("Restarting {}...".format(adjusted[0]))
    # We got an update here - let's call the subprocess, communicate, and
    # exit when it does

    p = subprocess.Popen([sys.executable,os.path.join(target_dir,adjusted[0])]+sys.argv[1:])
    p.communicate()
    exit(p.returncode)

def check_path(path):
    # Let's loop until we either get a working path, or no changes
    test_path = path
    last_path = None
    while True:
        # Bail if we've looped at least once and the path didn't change
        if last_path != None and last_path == test_path: return None
        last_path = test_path
        # Check if we stripped everything out
        if not len(test_path): return None
        # Check if we have a valid path
        if os.path.exists(test_path):
            return os.path.abspath(test_path)
        # Check for quotes
        if test_path[0] == test_path[-1] and test_path[0] in ('"',"'"):
            test_path = test_path[1:-1]
            continue
        # Check for a tilde and expand if needed
        if test_path[0] == "~":
            tilde_expanded = os.path.expanduser(test_path)
            if tilde_expanded != test_path:
                # Got a change
                test_path = tilde_expanded
                continue
        # Let's check for spaces - strip from the left first, then the right
        if test_path[0] in (" ","\t"):
            test_path = test_path[1:]
            continue
        if test_path[-1] in (" ","\t"):
            test_path = test_path[:-1]
            continue
        # Maybe we have escapes to handle?
        test_path = "\\".join([x.replace("\\", "") for x in test_path.split("\\\\")])

def chmod(path):
    # Takes a directory path, then chmod +x /that/path/*.command
    if not os.path.exists(path): return
    accepted = (".command",".sh",".py")
    if not os.path.isdir(path):
        # sent a file - just chmod that
        run_command(["chmod", "+x", path])
        return
    # Iterate all files in the dir and chmod the applicable ones
    cwd = os.getcwd()
    os.chdir(path)
    for f in os.listdir(path):
        if any(f for x in accepted if f.lower().endswith(x.lower())):
            # Found an acceptable file
            run_command(["chmod", "+x", f])
    os.chdir(cwd)

def cls():
   	os.system('cls' if os.name=='nt' else 'clear')

def head(text = "One Script", width = 55):
    cls()
    print("  {}".format("#"*width))
    mid_len = int(round(width/2-len(text)/2)-2)
    middle = " #{}{}{}#".format(" "*mid_len, text, " "*((width - mid_len - len(text))-2))
    if len(middle) > width+1:
        # Get the difference
        di = len(middle) - width
        # Add the padding for the ...#
        di += 3
        # Trim the string
        middle = middle[:-di] + "...#"
    print(middle)
    print("#"*width)

def update(
    repos,
    skip_clone=False,
    skip_pull=False,
    skip_reset=False,
    skip_chmod=False,
    list_modified=False,
    delete_modified=None,
    restore_modified=False,
    omit_mode_changes=False):

    head("Checking {} Repo{}".format(len(repos), "" if len(repos) == 1 else "s"))
    print(" ")
    if any((skip_clone,skip_reset,skip_chmod and os.name!="nt",skip_pull,list_modified,isinstance(delete_modified, re.Pattern))):
        if skip_clone:
            print(" - Not cloning missing repos")
        if skip_chmod and os.name!="nt":
            print(" - Not running 'chmod +x' on .command, .sh, and .py files")
        if skip_reset:
            print(" - Not resetting existing repos")
        if skip_pull:
            print(" - Not pulling existing repos")
        if list_modified:
            print(" - Listing modified files{}".format(
                " (only non-mode changes)" if omit_mode_changes else ""
            ))
        if isinstance(delete_modified, re.Pattern):
            if delete_modified.pattern == ".*":
                print(" - {} all modified files{}".format(
                    "Restoring" if restore_modified else "Deleting",
                    " (only non-mode changes)" if omit_mode_changes else ""
                ))
            else:
                print(" - {} modified files{} matching: {}".format(
                    "Restoring" if restore_modified else "Deleting",
                    " (only non-mode changes)" if omit_mode_changes else "",
                    delete_modified.pattern
                ))
        print(" ")
    for count,repo in enumerate(sorted(repos, key=lambda x: os.path.basename(x).lower()),start=1):
        out = None
        print("{} of {} - {}...".format(count,len(repos),os.path.basename(repo)))
        if not os.path.exists(os.path.join(os.getcwd(), os.path.basename(repo))):
            if not skip_clone:
                # Doesn't exist - git clone that shiz
                print(" - Cloning repo...")
                out = run_command(["git", "clone", repo])
        else:
            # Exists - let's update it
            cwd = os.getcwd()
            os.chdir(os.path.basename(repo))
            if list_modified or isinstance(delete_modified,re.Pattern):
                # We're removing entries labeled modified by git status
                # Let's get a list of affected files
                status = run_command(["git","status"])[0].split("\n")
                modified = [x.split("\tmodified:   ")[1].strip() for x in status if x.startswith("\tmodified:   ")]
                if omit_mode_changes:
                    # Only get changes that are not "old mode xxxx"/"new mode xxxx"
                    modified_non_mode = []
                    for m in modified:
                        mod = run_command(["git","diff",m])[0].strip().split("\n")[1:]
                        if any((not x.startswith(("old mode ","new mode ")) for x in mod)):
                            modified_non_mode.append(m)
                    modified = modified_non_mode
                # Iterate the qualified modified list
                if modified:
                    if list_modified:
                        print(" - Modified Files:")
                        print("\n".join(["    {}".format(x) for x in modified]))
                    if delete_modified is not None:
                        # Let's find our matches based on our regex
                        matched = [x for x in modified if delete_modified.fullmatch(x)]
                        if matched:
                            print(" - {} Matched Modified Files:".format("Restoring" if restore_modified else "Deleting"))
                            print("\n".join(["    {}".format(x) for x in matched]))
                            for m in matched:
                                if restore_modified:
                                    res = run_command(["git","restore",m])
                                    if res[2] != 0:
                                        print(" --> Failed to restore {}: {}".format(m,res[1]))
                                else:
                                    try:
                                        os.remove(m)
                                    except Exception as e:
                                        print(" --> Failed to delete {}: {}".format(m,e))
            if not skip_reset:
                # Only reset the repo if allowed
                print(" - Resetting repo...")
                run_command(["git", "reset", "--hard"])
            if not skip_pull:
                print(" - Pulling changes...")
                out = run_command(["git", "pull"])
            os.chdir(cwd)
        if out is not None:
            output = (out[0] if out[2]==0 else out[1]).rstrip()
            if output: print(output)
        print("")
        # Set perms
        if not skip_chmod and os.name!="nt":
            chmod(os.path.join(os.getcwd(), os.path.basename(repo)))

def check_git():
    # Make sure we have git available
    return run_command(["where" if os.name=="nt" else "which", "git"])[0].split("\n")[0].strip()

def main(
    settings_file=None,
    skip_clone=False,
    skip_pull=False,
    skip_update=False,
    skip_reset=False,
    skip_chmod=False,
    list_modified=False,
    delete_modified=None,
    restore_modified=False,
    omit_mode_changes=False,
    include=None,
    exclude=None):

    return_code = 0
    if not check_git():
        return_code = 1
        head("Git Not Found")
        print("")
        print("The 'git' command was not found in your PATH.  Please download")
        print("and install it from the following URL:")
        print("")
        if os.name=="nt":
            print("https://git-scm.com/download/win")
        elif sys.platform=="darwin":
            print("https://git-scm.com/download/mac")
        else:
            print("https://git-scm.com/download")
        print("")
    else:
        # Gather all repos
        head("Gathering Preliminary Info...")
        print("")
        if settings_file:
            print("Using settings from:\n - {}\n".format(settings_file))
        if skip_update:
            print("Skipping OneScript update check due to --skip-update override...\n")
        else:
            if not check_update():
                # Failed to check for updates
                if os.name=="nt": # Pause on Windows to keep the error on screen
                    input("\nPress [enter] to continue...")
                exit(1)
            print("")
        print("Gathering repo info...")
        page = 1
        repos = []

        # Ensure include and exclude are lowered lists if passed
        def normalize_list(l):
            if isinstance(l,str):
                return [str(x).strip() for x in l.lower().split(",")]
            elif isinstance(l,list):
                return [str(x).lower() for x in l]
            return None
        include = normalize_list(include)
        exclude = normalize_list(exclude)

        while True:
            try:
                # Generate our new URL and use a page count
                page_url = "{}&page={}".format(repo_url,page)
                print(" - {}".format(page_url))
                # Load the json data from the page_url
                page_repos = json.loads(_get_string(page_url))
                if not page_repos:
                    # If we didn't get anything bail
                    break
                # Keep track of how many we got
                per_page_count = len(page_repos)
                # Adjust according to include/exclude lists
                if isinstance(include,list):
                    page_repos = [x for x in page_repos if x["name"].lower() in include]
                if isinstance(exclude,list):
                    page_repos = [x for x in page_repos if x["name"].lower() not in exclude]
                # Get a list of URLs from the page_repos loaded this time around
                repo_urls = [x["html_url"] for x in page_repos if not x["name"] in skip_repos]
                # Add the new URLs to our repo list
                repos += repo_urls
                if not per_page_count >= per_page:
                    # Didn't get a full page of repos - no need to check
                    # for the next page.  Bail
                    break
            except Exception as e:
                print(" --> Failed to get info: {}".format(e))
                break
            page += 1
        print("")
        if not repos:
            print("No repos located - nothing to do.\n")
            return_code = 1
        else:
            cwd = os.getcwd()
            os.chdir(os.path.dirname(os.path.realpath(__file__)))
            try:
                update(
                    repos,
                    skip_clone=skip_clone,
                    skip_pull=skip_pull,
                    skip_reset=skip_reset,
                    skip_chmod=skip_chmod,
                    list_modified=list_modified,
                    delete_modified=delete_modified,
                    restore_modified=restore_modified,
                    omit_mode_changes=omit_mode_changes
                )
            except Exception as e:
                return_code = 1
                print("Something went wrong: {}".format(e))
                print("")
            os.chdir(cwd)
    print("Done.\n")
    if os.name == "nt":
        input("Press [enter] to exit...") # Let the user exit on Windows
    exit(return_code)

if __name__ == '__main__':
    # Setup the cli args
    parser = argparse.ArgumentParser(prog="OneScript", description="OneScript - a little script to update some other scripts.")
    parser.add_argument("-c", "--skip-clone", help="skip running 'git clone' for missing repos", action="store_true")
    parser.add_argument("-p", "--skip-pull", help="skip running 'git pull' for existing repos", action="store_true")
    parser.add_argument("-u", "--skip-update", help="skip checking for OneScript updates", action="store_true")
    parser.add_argument("-r", "--skip-reset", help="skip running 'git reset --hard' for each repo before 'git pull'", action="store_true")
    parser.add_argument("-d", "--skip-chmod", help="skip running 'chmod +x' on .command, .sh, and .py files when not running on Windows", action="store_true")
    parser.add_argument("-a", "--skip-all", help="applies all --skip-xxxx switches (equivalent to -c -p -u -r -d)", action="store_true")
    parser.add_argument("-l", "--list-modified", help="List modified files reported by 'git status'", action="store_true")
    parser.add_argument("-m", "--delete-modified", help="remove all files reported as modified by 'git' before updating (equivalent to '-x \".*\"')", action="store_true")
    parser.add_argument("-x", "--delete-modified-regex", help="remove files reported as modified by 'git status' that match the passed regex filter before updating (overrides -m)")
    parser.add_argument("-s", "--restore-modified", help="uses 'git restore <file>' instead of deleting", action="store_true")
    parser.add_argument("-o", "--omit-mode-changes", help="do not consider mode changes for modified files", action="store_true")
    parser.add_argument("-i", "--include", help="comma delimited list of repo names to include (if found)")
    parser.add_argument("-e", "--exclude", help="comma delimited list of repo names to exclude (if found)")
    parser.add_argument("settings_file", nargs="?", help="optional path to a JSON file containing settings to apply (overrides other args where defined)")

    args = parser.parse_args()

    if args.settings_file:
        settings_file = check_path(args.settings_file)
        if not settings_file:
            print("Invalid settings file passed:\n - {} does not exist".format(args.settings_file))
            exit(1)
        if not os.path.isfile(settings_file):
            print("Invalid settings file passed:\n - {} is not a file".format(settings_file))
            exit(1)
        try:
            new_settings = json.load(open(settings_file))
        except Exception as e:
            print("Invalid settings file passed:\n - {}".format(e))
            exit(1)
        # We got something - make sure it's a dict top-level
        if not isinstance(new_settings,dict):
            print("Invalid settings file passed:\n - Invalid format")
            exit(1)
        # Retain the full settings_file path at this point
        args.settings_file = settings_file
        # Now let's go through our settings and adjust them accordingly
        arg_list = (
            "skip_pull",
            "skip_update",
            "skip_reset",
            "skip_chmod",
            "skip_all",
            "list_modified",
            "delete_modified",
            "delete_modified-regex",
            "restore_modified",
            "omit_mode_changes",
            "include",
            "exclude"
        )
        CLASS_BOOL = type(True)
        CLASS_NONE = type(None)
        CLASS_LIST = type([])
        CLASS_STR  = type("")
        allowed_types = {
            "delete_modified_regex": (
                CLASS_NONE,
                CLASS_STR
            ),
            "include": (
                CLASS_NONE,
                CLASS_STR,
                CLASS_LIST
            ),
            "exclude": (
                CLASS_NONE,
                CLASS_STR,
                CLASS_LIST
            )
        }
        types_to_names = {
            CLASS_BOOL: "true/false",
            CLASS_NONE: "null",
            CLASS_LIST: "list of strings",
            CLASS_STR:  "string"
        }
        for a in arg_list:
            if not a in new_settings:
                continue # Skip missing args
            # Make sure it's the right type
            allowed = allowed_types.get(a,(CLASS_BOOL,))
            if not type(new_settings[a]) in allowed:
                # Nope
                print("Invalid settings file passed:\n - '{}' can only be of types: {}".format(
                    a,
                    ", ".join([types_to_names.get(x,x) for x in allowed])
                ))
                exit(1)
            # Set it locally
            setattr(args,a,new_settings[a])

    if args.skip_all:
        args.skip_clone = True
        args.skip_pull = True
        args.skip_update = True
        args.skip_reset = True
        args.skip_chmod = True

    delete_modified = None # Initialize with None
    if args.delete_modified_regex:
        # We need to ensure the regex is valid
        try:
            delete_modified = re.compile(args.delete_modified_regex)
        except Exception as e:
            print("Invalid regex passed to --delete-modified-regex:\n - {}".format(e))
            exit(1)
    elif args.delete_modified or args.restore_modified:
        # We're not passing regex - but we still need to use regex to match names
        # We'll just allow all with .*
        delete_modified = re.compile(".*")

    # Start our main function
    main(
        settings_file=args.settings_file,
        skip_clone=args.skip_clone,
        skip_pull=args.skip_pull,
        skip_update=args.skip_update,
        skip_reset=args.skip_reset,
        skip_chmod=args.skip_chmod,
        list_modified=args.list_modified,
        delete_modified=delete_modified,
        restore_modified=args.restore_modified,
        omit_mode_changes=args.omit_mode_changes,
        include=args.include,
        exclude=args.exclude
    )

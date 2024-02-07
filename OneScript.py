#!/usr/bin/env python
# 0.0.28
import os, subprocess, shlex, datetime, sys, json, ssl

# Python-aware urllib stuff
if 2/3!=0:
    from urllib.request import urlopen
else:
    # Import urllib2 to catch errors
    import urllib2
    from urllib2 import urlopen
    input = raw_input

os.chdir(os.path.dirname(os.path.realpath(__file__)))

skiprepos = ("OneScript","Hackintosh-Guide","Hackintosh-Tips-And-Tricks","CorpBot-Docker","camielbot","OpenCorePkg")
repourl = "https://api.github.com/users/corpnewt/repos?per_page=100"
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
    # Checks against https://raw.githubusercontent.com/corpnewt/OneScript/master/OneScript.command to see if we need to update
    head("Checking for Updates")
    print(" ")
    with open(os.path.realpath(__file__), "r") as f:
        # Our version should always be the second line
        version = get_version(f.read())
    print("Current version: {}".format(version))
    try:
        new_py = _get_string(base_url.format(file_list[0]))
        new_version = get_version(new_py)
        print(" Remote version: {}".format(new_version))
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
            print(" - Checking {}...".format(f))
            if not os.path.exists(f):
                print(" --> Skipped (not found locally)...")
                continue # Don't update files we don't have
            print(" --> Downloading...")
            file_contents = _get_string(base_url.format(file_list[i]))
            print(" --> Replacing...")
            with open(f, "w") as x:
                x.write(file_contents)
            # chmod +x on non-Windows, then restart
            if os.name!="nt" and not f.lower().endswith(".bat"):
                print(" --> Setting executable mode...")
                run_command(["chmod", "+x", f])
    except Exception as e:
        print("Error gathering files:\n{}".format(e))
        return
    print("")
    print("Restarting {}...".format(adjusted[0]))
    os.execv(sys.executable,[sys.executable,'"'+adjusted[0]+'"']+sys.argv[1:])

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

def custom_quit():
    head()
    print("by CorpNewt\n")
    print("Thanks for testing it out, for bugs/comments/complaints")
    print("send me a message on Reddit, or check out my GitHub:\n")
    print("www.reddit.com/u/corpnewt")
    print("www.github.com/corpnewt\n")
    # Get the time and wish them a good morning, afternoon, evening, and night
    hr = datetime.datetime.now().time().hour
    if hr > 3 and hr < 12:
        print("Have a nice morning!\n\n")
    elif hr >= 12 and hr < 17:
        print("Have a nice afternoon!\n\n")
    elif hr >= 17 and hr < 21:
        print("Have a nice evening!\n\n")
    else:
        print("Have a nice night!\n\n")
    exit(0)

def update():
    if not check_update() and os.name=="nt": # Pause on Windows to keep the error on screen
        input("\nPress [enter] to continue...")
    head("Checking {} Repo{}".format(len(repos), "" if len(repos) == 1 else "s"))
    print(" ")
    count = 0
    for repo in sorted(repos, key=lambda x: os.path.basename(x).lower()):
        count += 1
        if not os.path.exists(os.path.join(os.getcwd(), os.path.basename(repo))):
            # Doesn't exist - git clone that shiz
            print("{} of {} - Cloning {}...".format(count, len(repos), os.path.basename(repo)))
            out = run_command(["git", "clone", repo])
        else:
            # Exists - let's update it
            print("{} of {} - Updating {}...".format(count, len(repos), os.path.basename(repo)))
            cwd = os.getcwd()
            os.chdir(os.path.basename(repo))
            out = run_command(["git", "reset", "--hard"])
            out = run_command(["git", "pull"])
            os.chdir(cwd)
        print(out[0] if out[2] == 0 else out[1])
        # Set perms
        if os.name!="nt": chmod(os.path.join(os.getcwd(), os.path.basename(repo)))

# Gather all repos
head("Gathering Repo Info...")
print("")
print(repourl)
print("")
all_repos = json.loads(_get_string(repourl))
repos = [x["html_url"] for x in all_repos if not x["name"] in skiprepos]

def main():
    update()
    if os.name == "nt": input("Press [enter] to exit...") # Let the user exit on Windows
    custom_quit()


if __name__ == '__main__':
    main()

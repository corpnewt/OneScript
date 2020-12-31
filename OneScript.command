#!/usr/bin/env python
# 0.0.21
import os, subprocess, shlex, datetime, sys, json, ssl

# Python-aware urllib stuff
if sys.version_info >= (3, 0):
    from urllib.request import urlopen
else:
    # Import urllib2 to catch errors
    import urllib2
    from urllib2 import urlopen
    input = raw_input

os.chdir(os.path.dirname(os.path.realpath(__file__)))

skiprepos = ("OneScript","Hackintosh-Guide","Hackintosh-Tips-And-Tricks","CorpBot-Docker","camielbot")
repourl = "https://api.github.com/users/corpnewt/repos?per_page=100"
url = "https://raw.githubusercontent.com/corpnewt/OneScript/master/OneScript.command"

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
        if c == None:
            return ("", "Command not found!", 1)
        return (c[0].decode("utf-8", "ignore"), c[1].decode("utf-8", "ignore"), p.returncode)

def open_url(url):
    # Wrap up the try/except block so we don't have to do this for each function
    try:
        response = urlopen(url)
    except Exception as e:
        if sys.version_info >= (3, 0) or not (isinstance(e, urllib2.URLError) and "CERTIFICATE_VERIFY_FAILED" in str(e)):
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
    try:
        total_size = int(response.headers['Content-Length'])
    except:
        total_size = -1
    chunk_so_far = "".encode("utf-8")
    while True:
        chunk = response.read(CHUNK)
        bytes_so_far += len(chunk)
        if not chunk:
            break
        chunk_so_far += chunk
    return chunk_so_far.decode("utf-8")

def get_version(text):
    try:
        return text.split("\n")[1][2:]
    except:
        return "Unknown"

def need_update(new, curr):
    for i in range(len(curr)):
        if int(new[i]) < int(curr[i]):
            return False
        elif int(new[i]) > int(curr[i]):
            return True
    return False

def check_update():
    # Checks against https://raw.githubusercontent.com/corpnewt/OneScript/master/OneScript.command to see if we need to update
    head("Checking for Updates")
    print(" ")
    with open(os.path.realpath(__file__), "r") as f:
        # Our version should always be the second line
        version = get_version(f.read())
    print(version)
    try:
        new_text = _get_string(url)
        new_version = get_version(new_text)
    except:
        # Not valid json data
        print("Error checking for updates (network issue)")
        return

    if version == new_version:
        # The same - return
        print("v{} is already current.".format(version))
        return True
    # Split the version number
    try:
        v = version.split(".")
        cv = new_version.split(".")
    except:
        # not formatted right - bail
        print("Error checking for updates (version string malformed)")
        return

    if not need_update(cv, v):
        print("v{} is already current.".format(version))
        return True

    # Update
    with open(os.path.realpath(__file__), "w") as f:
        f.write(new_text)

    # chmod +x on non-Windows, then restart
    if os.name!="nt": run_command(["chmod", "+x", __file__])
    os.execv(sys.executable, [sys.executable,__file__]+sys.argv)

def chmod(path):
    # Takes a directory path, then chmod +x /that/path/*.command
    if not os.path.exists(path):
        return
    accepted = [ ".command", ".sh", ".py" ]
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
    for repo in sorted(repos, key=lambda x: os.path.basename(x)):
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

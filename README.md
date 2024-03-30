# OneScript
A little script to update some other scripts

***

```
usage: OneScript [-h] [-c] [-p] [-u] [-r] [-d] [-a] [-l] [-m]
                 [-x DELETE_MODIFIED_REGEX] [-s] [-o] [-i INCLUDE]
                 [-e EXCLUDE]

OneScript - a little script to update some other scripts.

options:
  -h, --help            show this help message and exit
  -c, --skip-clone      skip running 'git clone' for missing repos
  -p, --skip-pull       skip running 'git pull' for existing repos
  -u, --skip-update     skip checking for OneScript updates
  -r, --skip-reset      skip running 'git reset --hard' for each repo before
                        'git pull'
  -d, --skip-chmod      skip running 'chmod +x' on .command, .sh, and .py
                        files when not running on Windows
  -a, --skip-all        applies all --skip-xxxx switches (equivalent to -c -p
                        -u -r -d)
  -l, --list-modified   List modified files reported by 'git status'
  -m, --delete-modified
                        remove all files reported as modified by 'git' before
                        updating (equivalent to '-x ".*"')
  -x DELETE_MODIFIED_REGEX, --delete-modified-regex DELETE_MODIFIED_REGEX
                        remove files reported as modified by 'git status' that
                        match the passed regex filter before updating
                        (overrides -m)
  -s, --restore-modified
                        uses 'git restore <file>' instead of deleting
  -o, --omit-mode-changes
                        do not consider mode changes for modified files
  -i INCLUDE, --include INCLUDE
                        comma delimited list of repo names to include (if
                        found)
  -e EXCLUDE, --exclude EXCLUDE
                        comma delimited list of repo names to exclude (if
                        found)
```

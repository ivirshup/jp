# jp

CLI utils for jupyter.

```sh
$ jp list  # returns running kernels
$ jp join {name}  # Creates jupyter console session attached to kernel
$ jp open {pth}  # Open path in server. Will open notebooks or directories
```

## Tab completion (only tested with zsh)

This tool uses `click`, so follow what that does: https://click.palletsprojects.com/en/7.x/bashcomplete/#activation

For `zsh` either:

### 1

Add `eval "$(_JP_COMPLETE=source_zsh jp)"` to your `.zshrc`.

### 2

Generate a completion script with:

```zsh
_JP_COMPLETE=source_zsh jp > jp-complete.sh
```

Then run that from `.zshrc`

```zsh
. /path/to/jp-complete.sh
```

## TODO

- [x] Better tab completion, and with `zsh` support
    - [ ] Can I get this with argparse?
- [ ] Specify port when multiple servers are running
- [ ] Check how well this works with jupyter lab
- [ ] Tests

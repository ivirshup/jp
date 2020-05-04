# jp

CLI utils for jupyter.

```sh
$ jp list  # returns running kernels
$ jp join {name}  # Creates jupyter console session attached to kernel
$ jp open {pth}  # Open path in server. Will open notebooks or directories
```

## TODO

- [ ] Better tab completion, and with `zsh` support
    - [ ] Can I get this with argparse?
- [ ] Specify port when multiple servers are running
- [ ] Check how well this works with jupyter lab
- [ ] Tests

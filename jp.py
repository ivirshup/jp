#!/usr/local/bin/python3
"""Script to work with jupyter notebooks.

Will require notebook server token (possibly store this by setting environment variable on server start)

Will use [server api](https://github.com/jupyter/jupyter/wiki/Jupyter-Notebook-Server-API)

Things I want this to do:

* List existing kernels
* Join one of the existing kernels
    * With a terminal
    * With a notebook
"""

import json
from shutil import get_terminal_size
from subprocess import run, PIPE
from pathlib import Path

import requests
from tabulate import tabulate


class ServerInterface(object):
    def __init__(self, data):
        self._data = data
        self.url = data["url"]
        self.token = data["token"]
        self.root_dir = data["root_dir"]

    def running_kernels(self):
        full_url = f"{self.url}api/sessions?token={self.token}"
        return requests.get(full_url).json()


# TODO: Better error messages
def running_server(port=None) -> ServerInterface:
    """
    Returns object describing running server.
    """
    p = run(["jupyter", "notebook", "list", "--json"], stdout=PIPE)
    procs = list(map(json.loads, p.stdout.decode("utf-8").split("\n")[:-1]))
    user_home = str(Path.home())

    if port is None and len(procs) > 1:
        # Heuristic for default home.
        procs = [x for x in procs if x["root_dir"].startswith(user_home)]
    else:
        procs = [x for x in procs if x["port"] == int(port)]
    if len(procs) == 1:
        return ServerInterface(procs[0])
    elif len(procs) == 0:
        raise OSError("No jupyter servers could be found!")
    else:
        procs_rep = "\n\t".join(map(str, procs))
        raise NotImplementedError(
            f"{len(procs)} servers found! Not able to tell which one to use from:\n\n\t{procs_rep}"
        )


def show_running_kernels(kernels, *, verbose: int = 0):
    paths = [x["path"] for x in kernels]
    table = {
        "KernelName": [Path(x).stem for x in paths],
        "Kernel": [x["kernel"]["name"] for x in kernels],
    }
    if verbose:
        table["Path"] = [str(x) for x in paths]
    if verbose == 1:  # Make sure table prints to terminal width
        lines = tabulate(table, headers="keys").splitlines()
        col_limit = get_terminal_size().columns
        col_max = max(map(len, lines))
        path_col_idx = lines[0].rfind("Path")
        if col_max > col_limit:
            path_col_size = col_limit - path_col_idx
            table["Path"] = [
                "..." + x[-path_col_size + 3 :] if len(x) > path_col_size else x
                for x in table["Path"]
            ]
    return tabulate(table, headers="keys")


def kernel_lookup(kernels, name):
    matching_kernels = []
    for kernel in kernels:
        if Path(kernel["path"]).stem == name:
            matching_kernels.append(kernel)
    if len(matching_kernels) == 0:
        raise Exception(f"No kernels with name '{name}' found.")
    elif len(matching_kernels) > 1:
        raise Exception(f"More than one kernel with name '{name}' found.")
    return matching_kernels[0]


# TODO, should this also start a kernel?
def create_notebook(path):
    s = running_server()
    surl = s.url
    token = s.token
    r = requests.put(
        f"{surl}api/contents/{str(path)}?token={token}", json={"format": "json"}
    )
    if r.status_code != 201:
        raise Exception(
            f"Could not create notebook at {path}. \n Recieved error: {r.status_code} for: {r.content}"
        )
    return r


def format_kernel_json(kernel_dict):
    return f"kernel-{kernel_dict['kernel']['id']}.json"


import click

port = click.option(
    "--port", help="Port used by jupyter server.", default="8888", is_eager=True
)


@click.group()
def cli():
    pass


@cli.command(name="list", help="List running kernels")
@port
@click.option("-v", "--verbose", help="Increase verbosity", count=True)
def list_kernels(*, port, verbose):
    s = running_server(port)
    click.echo(show_running_kernels(s.running_kernels(), verbose=verbose))


def running_arg_complete(ctx, args, incomplete):
    """Argument completion for `jp join`"""
    from click.shell_completion import CompletionItem

    # TODO: There must be a better way to get default values
    port = ctx.params["port"] if ctx.params.get("port", None) is not None else "8888"
    kernels = running_server(port).running_kernels()
    matching_kernels = []
    for kernel in kernels:
        name = Path(kernel["path"]).stem
        if incomplete in name:
            path = kernel["path"]
            kernel_type = kernel["kernel"]["name"]
            matching_kernels.append(
                CompletionItem(name, help=f"{kernel_type} at '{path}'")
            )

    return matching_kernels


@cli.command(name="join", help="Join an existing kernel by name")
@click.argument("name", type=click.STRING, shell_complete=running_arg_complete)
@port
def join_kernel(name, *, port):
    """Join running kernel by notebook name."""
    s = running_server(port)
    kernels = s.running_kernels()
    to_join = kernel_lookup(kernels, name)
    command = ["jupyter", "console", "--existing", format_kernel_json(to_join)]
    run(command)


@cli.command(name="kill", help="Kill an running kernel.")
@click.argument("name", type=click.STRING, shell_complete=running_arg_complete)
@port
def kill_kernel(name, *, port):
    s = running_server(port)
    kernels = s.running_kernels()
    to_kill = kernel_lookup(kernels, name)
    r = requests.delete(f"{s.url}api/kernels/{to_kill['kernel']['id']}?token={s.token}")
    return r


@cli.command(name="open", help="Open jupyter notebook browser at path.")
@click.argument("path", required=False, type=click.Path())
@port
def open_browser(path=None, *, port):
    s = running_server(port)
    if path is None:
        path = "."

    abs_path = Path(path).absolute()
    rel_path = abs_path.relative_to(s.root_dir)

    if abs_path.is_dir():
        url = f"{s.url}tree/{rel_path}"
    elif abs_path.is_file() and abs_path.suffix == ".ipynb":
        url = f"{s.url}notebooks/{rel_path}"
    else:
        raise ValueError(f"Unable to open notebook at {abs_path}")

    run(["open", url])


if __name__ == "__main__":
    cli()

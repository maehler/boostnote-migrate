# Migrate notes from Boostnote to Boost Note

The aim of this script is to migrate notes from the old version of Boostnote to the newer version that only uses cloud storage.
Notes from the old version (in `.cson`) are parsed and uploaded into folders with the same names as in the previous version (given that you have the `boostnote.json` file available).

## Prerequisites

- Python >=3.9
- click
- cson

A conda environment is available in the repository ([`environment.yaml`](environment.yaml)), and this has all the dependencies in it.
Install it by running

```sh
conda env create -f environment.yaml
```

## Setup

It uses [the public Boost Note API](https://intercom.help/boostnote-for-teams/en/articles/4590937-public-api-documentation) in order to accomplish this, and in order for it to work, you need to get an API key for the team where you would like to migrate your notes. See [the API documentation](https://intercom.help/boostnote-for-teams/en/articles/4590937-public-api-documentation) for instructions on how to generate a key.
Once you have the key, you can add it to the `config.ini` file in this repository.

```ini
[<team name>]
api_key = <your api key here>
```

This way, you can have it set up for multiple teams, if you would like.
If you have multiple teams set up, the first team listed will be acted upon by default, but this behaviour can be changed with the `--team` argument.

## Usage

### List teams

If you are like me, and forget what teams you've added to the config file, you can list them from the command line.

```sh
python boostnote-migrate.py teams
```

### Workspaces

The top-level folders in each team are called workspaces (confusing, I know).

```sh
python boostnote-migrate.py workspaces
```

By default, this lists the workspaces for the first team that you have listed in your config file.
You can change this by supplying the `-t/--team` argument.

```sh
python boostnote-migrate.py --team "My other team" workspaces
```

### Folders

Listing of folders within a team.

```sh
python boostnote-migrate.py folders list
```

Creating a new folder.

```sh
python boostnote-migrate.py folders new "Name of my new folder"
```

### Documents

Create a new document from scratch.

```sh
python boostnote-migrate.py docs new \
	--content "Content of my new note" \
	"Title of my note"
```

By default, this will be added to the first workspace of the default team, but you can change what team to add it to (`-t/--team`), and/or what workspace to add it to (`-w/--workspace-id`).

You can also import documents from the previous version of Boostnote to a particular workspace:

```sh
python boostnote-migrate.py docs import \
	--json /path/to/boostnote.json \
	--workspace-id <workspace-id> \
	/path/to/notes/old_note.cson
```

... or to a particular folder:

```sh
python boostnote-migrate.py docs import \
	--json /path/to/boostnote.json \
	--folder-id <folder-id> \
	/path/to/notes/old_note.cson
```

The `--json` argument is optional.
What it does is to put any imported notes in a folder with the same name as where it came from.
Without this argument, the note will simply be a direct child of the workspace/folder that it is added to.

The folder and workspace IDs can be obtained with the commands listed earlier in this document.

## Caveats

- Snippets are not handled.
You will get an error message saying the note doesn't have any content.
- Hyperlinks between notes are not resolved.
- Error handling is quite rough, and corner-cases have not been extensively tested.
Actually, not much testing at all has been done since this was meant as something quick and dirty that I could use to migrate my old notes.
- Building on the previous point, this was made for my needs, and YMMV.
Use with caution!
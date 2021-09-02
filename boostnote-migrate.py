import click
import configparser
import cson
import json
import sys
import urllib.error
import urllib.parse
import urllib.request as request

API_BASE_URL = 'https://boostnote.io/api'

def get_header(ctx):
	return {
		'Authorization': f'Bearer {ctx.obj["api_key"][ctx.obj["team"]]}',
		'Content-type': 'application/json'
	}

def get_spaces(ctx):
	r = request.Request(f'{API_BASE_URL}/workspaces',
		headers = get_header(ctx))
	
	workspaces = {}
	with request.urlopen(r) as response:
		for space in json.loads(response.read())['workspaces']:
			workspaces[space['id']] = space

	return workspaces

def get_folders(ctx):
	r = request.Request(f'{API_BASE_URL}/folders',
		headers = get_header(ctx))

	folders = {}
	with request.urlopen(r) as response:
		for f in json.loads(response.read())['folders']:
			folders[f['id']] = f
	
	return folders

def find_folder(ctx, name, workspace_id, parent_id):
	folders = get_folders(ctx)

	for id, f in folders.items():
		if f['name'] == name and f['workspaceId'] == workspace_id and f['parentFolderId'] == parent_id:
			return id
	
	return None

def create_folder(ctx, name, workspace, private=False):
	data_dict = {
		'name': name,
		'workspaceId': workspace
	}

	if not private:
		data_dict['public'] = 'true'

	data = json.dumps(data_dict).encode('utf-8')

	r = request.Request(f'{API_BASE_URL}/folders',
		data=data,
		method='POST',
		headers=get_header(ctx))

	try:
		response = request.urlopen(r)
	except urllib.error.HTTPError as e:
		print(e, file=sys.stderr)
		sys.exit(1)

	return json.loads(response.read())['folder']['id']

def create_document(ctx, title, content,
		workspace_id=None, folder_id=None, tags=None):
	data_dict = {
		'title': title,
		'content': content,	
	}

	if tags is not None:
		data_dict['tags'] = tags
	if folder_id is not None:
		data_dict['parentFolder'] = folder_id
	if workspace_id is not None:
		data_dict['workspaceId'] = workspace_id

	data = json.dumps(data_dict).encode('utf-8')

	# print(data)

	r = request.Request(f'{API_BASE_URL}/docs',
		data=data,
		method='POST',
		headers=get_header(ctx))

	try:
		response = request.urlopen(r)
	except urllib.error.HTTPError as e:
		print(e, file=sys.stderr)
		sys.exit(1)

	return json.loads(response.read())['doc']

def parse_cson(filename):
	with open(filename, 'rb') as f:
		doc = cson.load(f)
	
	if 'title' not in doc:
		print(f'error: no title found in document: {filename}',
			file=sys.stderr)
		sys.exit(1)
	
	if 'content' not in doc:
		print(f'error: no content found in document: {filename}',
			file=sys.stderr)
		sys.exit(1)
	
	return doc

def get_teams(ctx):
	for i, ws in enumerate(ctx.obj['api_key'].keys()):
		print(f'{i}: {ws}')

@click.group()
@click.option('-t', '--team')
@click.pass_context
def cli(ctx, team):
	config = configparser.ConfigParser()
	config.read('config.ini')
	ctx.ensure_object(dict)
	default_team = None
	ctx.obj['api_key'] = {}
	for k in config.keys():
		if 'api_key' not in config[k]:
			continue
		if default_team is None:
			default_team = k
		ctx.obj['api_key'][k] = config[k]['api_key']

	if team is None:
		ctx.obj['team'] = default_team
	else:
		if team not in ctx.obj['api_key']:
			print('error: team not found: {}'.format(team))
			sys.exit(1)
		ctx.obj['team'] = team

@cli.group()
@click.pass_context
def folders(ctx):
	pass

@folders.command('list')
@click.pass_context
def folders_list(ctx):
	""" List folders
	"""
	for id, f in get_folders(ctx).items():
		print(f'name: {f["name"]}\nid: {id}\nworkspace: {f["workspaceId"]}\n')

@folders.command('new')
@click.argument('name')
@click.option('-w', '--workspace-id', metavar='ID',
	help='id of workspace where folder should be created')
@click.option('-p', '--private', is_flag=True,
	help='create a private folder')
@click.pass_context
def folders_new(ctx, name, workspace_id, private):
	"""Create a new folder
	"""
	if workspace_id is None:
		print('error: workspace id required', file=sys.stderr)
		sys.exit(1)
	create_folder(ctx, name, workspace_id, private)

@cli.group()
@click.pass_context
def docs(ctx):
	pass

@docs.command('new')
@click.argument('title')
@click.option('-c', '--content',
	help='content of the note')
@click.option('-w', '--workspace-id', metavar='ID')
@click.option('-f', '--folder-id', metavar='ID')
@click.pass_context
def docs_new(ctx, title, content, workspace_id, folder_id):
	"""Create new document
	"""
	doc = create_document(ctx, title, content,
		workspace_id, folder_id)
	print(f'Created "{title}" ({doc["id"]}) in {doc["workspace"]["name"]}{doc["folderPathname"]}')

@docs.command('import')
@click.argument('filename')
@click.option('-j', '--json', 'boostnote_json', metavar='FILE',
	help='json file containing original folder information')
@click.option('-w', '--workspace-id', metavar='ID')
@click.option('-f', '--folder-id', metavar='ID')
@click.pass_context
def import_cson(ctx, filename, boostnote_json, workspace_id, folder_id):
	"""Import a cson document from old Boostnote
	"""
	if workspace_id is None and folder_id is None:
		print('error: either workspace id or folder id is required',
			file=sys.stderr)
		sys.exit(1)
	
	if workspace_id is not None and folder_id is not None:
		print('error: give only one id', file=sys.stderr)
		sys.exit(1)

	original_folders = {}
	if boostnote_json is not None:
		with open(boostnote_json, 'rb') as f:
			bn_json = json.load(f)
		if 'folders' not in bn_json:
			print('error: no folder information available: {}'.format(boostnote_json))
			sys.exit(1)
		for f in bn_json['folders']:
			original_folders[f['key']] = f['name']
	
	doc = parse_cson(filename)

	if len(original_folders) > 0 and 'folder' in doc:
		destination_folder = original_folders[doc['folder']]
		destination_folder_id = find_folder(ctx, destination_folder, workspace_id, folder_id)

		if destination_folder_id is None:
			destination_folder_id = create_folder(ctx, destination_folder, workspace_id)

		doc = create_document(ctx, doc['title'], doc['content'],
			workspace_id, destination_folder_id, tags=doc['tags'])
	else:
		doc = create_document(ctx, doc['title'], doc['content'],
			workspace_id, folder_id, tags=doc['tags'])
	
	print(f'Created "{doc["title"]}" ({doc["id"]}) in {doc["workspace"]["name"]}{doc["folderPathname"]}')

@cli.command()
@click.pass_context
def workspaces(ctx):
	for id, space in get_spaces(ctx).items():
		print(f'name: {space["name"]}\nid: {id}\n')

@cli.command()
@click.pass_context
def teams(ctx):
	get_teams(ctx)

if __name__ == '__main__':
	cli(obj={})
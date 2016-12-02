#!/usr/bin/python2
import os
import sys
import yaml
from subprocess import PIPE, Popen
from time import strftime
import pycurl
from cStringIO import StringIO

MODULE_PATH = '/etc/puppet/modules'
MODULE_STAGE_DIR = '/var/tmp/modules_stage' + strftime("-%d%m%Y-%H%M")
INPUT_ENV_VAR = 'EXTRA_PUPPET_MODULES_SAT'
PULP_URL = '/pulp/puppet/'

if not os.path.exists(MODULE_PATH):
  os.makedirs(MODULE_PATH)
if not os.path.exists(MODULE_STAGE_DIR):
  os.makedirs(MODULE_STAGE_DIR)

### Create loader for the Ruby object in puppet yaml
def construct_ruby_object(loader, suffix, node):
  return loader.construct_yaml_map(node)

def construct_ruby_sym(loader, node):
  return loader.construct_yaml_str(node)

yaml.add_multi_constructor(u'!ruby/object:', construct_ruby_object)
yaml.add_constructor(u'!ruby/sym', construct_ruby_sym)
###

def get_installed_modules(modulepath):
  #
  # Get list of installed modules
  #
  installed_modules = []
  data = yaml.load(Popen(( 'puppet', 'module', 'list',
                           '--modulepath', modulepath,
                           '--render-as', 'yaml'),
                           stdout=PIPE).communicate()[0])
  for module in data['modules_by_path'][modulepath]:
    installed_modules.append(module.get('name'))
  return installed_modules

def puppet_module_uninstall(module, module_path):
  #
  # Uninstall a puppet module
  #
  ps = Popen([ 'puppet', 'module', 'uninstall', '--force',
               '--modulepath', MODULE_PATH, module ])
  ps.communicate()
  return None

def puppet_module_install(modulePackage, modulePath):
  #
  # Install puppet module
  #
  ps = Popen([ 'puppet', 'module', 'install', '--ignore-dependencies',
               '--target-dir', modulePath, modulePackage ])
  ps.communicate()
  return None

def download_file(filePath, fileName, url):
  # Should decorate with try and catch exception, retry on connect errors?
  file = open(filePath + '/' + fileName, 'wb')
  curl = pycurl.Curl()
  curl.setopt(pycurl.URL, url)
  curl.setopt(pycurl.WRITEDATA, file)
  curl.perform()
  curl.close()
  file.close()
  return filePath + '/' + fileName

def get_metadata(url):
  buff = StringIO()
  curl = pycurl.Curl()
  curl.setopt(pycurl.URL, url + '/modules.json')
  curl.setopt(pycurl.WRITEFUNCTION, buff.write)
  curl.perform()
  curl.close()
  metadata = yaml.safe_load(buff.getvalue())
  return metadata


data = yaml.safe_load(os.environ.get(INPUT_ENV_VAR))
installed_modules = get_installed_modules(MODULE_PATH)
base_url = ( '://'.join([ data.get('protocol'), data.get('server') ])
             + PULP_URL + '-'.join([ data.get('organization'),
                                     data.get('environment'),
                                     data.get('content_view') ]) )
metadata = get_metadata(base_url)
for module in data.get('modules'):
  author = module.split('-')[0]
  name = module.split('-')[1]

  # Get version of module, need it to build module_filename
  version = False
  for entry in metadata:
    if entry.get('author') == author and entry.get('name') == name:
      version = entry.get('version')
      break
  if not version:
    print "Module not in repository"
    sys.exit(1)

  # Download module
  module_path = '/'.join([ 'system', 'releases', author[0], author])
  module_filename = '-'.join([ author, name, version]) + '.tar.gz'
  module_url = '/'.join([ base_url, module_path, module_filename ])
  module_pkg = download_file(MODULE_STAGE_DIR, module_filename, module_url)

  if name in installed_modules:
    puppet_module_uninstall(module, MODULE_PATH)
  puppet_module_install(module_pkg, MODULE_PATH)


#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains ArtellaDrive utils classes and functions
"""

from __future__ import print_function, division, absolute_import

import os
import sys
import time
import json
import shutil
import fnmatch
import inspect
import logging
import importlib
import subprocess
from functools import wraps
try:
    from importlib.machinery import SourceFileLoader
except ImportError:
    import imp

logger = logging.getLogger('artella')


def is_python2():
    """
    Returns whether or not current version is Python 2
    :return: bool
    """

    return sys.version_info.major == 2


def is_python3():
    """
    Returns whether or not current version is Python 3
    :return: bool
    """

    return sys.version_info.major == 3


def is_windows():
    """
    Returns whether or not current OS platform is Windows

    :return: True if current platform is Windows; False otherwise.
    :rtype: bool
    """

    return sys.platform.startswith('win')


def is_mac():
    """
    Returns whether or not current OS platform is MacOS

    :return: True if current platform is MacOS; False otherwise.
    :rtype: bool
    """

    return sys.platform == 'darwin'


def is_linux():
    """
    Returns whether or not current OS platform is Linux

    :return: True if current platform is Linux; False otherwise.
    :rtype: bool
    """

    return 'linux' in sys.platform


def clean_path(path):
    """
    Returns a cleaned path to make sure that we do not have problems with path slashes
    :param str path: path we want to clean
    :return: clean path
    :rtype: str
    """

    # Convert '~' Unix char to user's home directory and remove spaces and bad slashes
    if is_python2():
        if isinstance(path, str):
            path = os.path.expanduser(path)
        else:
            path = os.path.expanduser(str(path.encode('utf-8')))
    path = str(path.replace('\\', '/').replace('//', '/').rstrip('/').strip())

    # Fix server paths
    is_server_path = path.startswith('\\')
    while '\\' in path:
        path = path.replace('\\', '//')
    if is_server_path:
        path = '//{}'.format(path)

    # Fix web paths
    if not path.find('https://') > -1:
        path = path.replace('//', '/')

    return path


def split_path(path, clean_drive=True):
    """
    Splits given paths in all its sub parts

    :param str path: Path we want to retrieve parts of
    :param clean_drive: True if we want to remove the drive from the result; False otherwise.
    :return: List of sub parts in the given path
    :rtype: list(str)
    """

    if clean_drive:
        path = os.path.splitdrive(path)[-1]

    return [next(part for part in path.split(os.path.sep) if part)]


def clear_list(list_to_clear):
    """
    Clears given Python list. Works fine for both Python 2 and Python 3.

    :param list_to_clear: list
    """

    if is_python2():
        del list_to_clear[:]
    else:
        list_to_clear.clear()


def force_list(var, remove_duplicates=False):
    """
    Returns given variable as a list

    :param object var: variable we want to convert into a list
    :param bool remove_duplicates: whether or not duplicated element should be removed from output list
    :return: Adds given variable into a list if the variable is not already a list. If the variable is None, an empty
        list is returned. If the variable is a tuple, the tuple is converted into a list
    :rtype: list(object)
    """

    if var is None:
        return list()

    if type(var) is not list:
        if type(var) in [tuple]:
            var = list(var)
        else:
            var = [var]

    if remove_duplicates:
        var = list(set(var))

    return var


def get_files(root_folder, pattern='*'):
    """
    Returns files found in given folder and sub folders taking into account the given pattern
    :param str root_folder: root folder where we want to start searching from
    :param str pattern: find pattern that we use to filter our search for specific file names or extensions
    :return: List of files located in given root folder hierarchy and with the given pattern
    :rtype: list(str)
    """

    if not root_folder or not os.path.isdir(root_folder):
        return list()

    files_found = list()

    for dir_path, dir_names, file_names in os.walk(root_folder):
        for file_name in fnmatch.filter(file_names, pattern):
            files_found.append(clean_path(os.path.join(dir_path, file_name)))

    return list(set(files_found))


def get_file_size(file_path, round_value=2):
    """
    Returns the size of the given file
    :param file_path: str
    :param round_value: int, value to round size to
    :return: str
    """

    size = os.path.getsize(file_path)
    size_format = round(size * 0.000001, round_value)

    return size_format


def open_folder(path):
    """
    Open folder using OS default settings
    :param path: str, folder path we want to open
    """

    if sys.platform.startswith('darwin'):
        subprocess.Popen(["open", path])
    elif os.name == 'nt':
        os.startfile(path)
    elif os.name == 'posix':
        subprocess.Popen(["xdg-open", path])
    else:
        raise NotImplementedError('OS not supported: {}'.format(os.name))


def open_file(file_path):
    """
    Open file using OS default settings
    :param file_path: str, file path we want to open
    """

    if sys.platform.startswith('darwin'):
        subprocess.call(('open', file_path))
    elif os.name == 'nt':
        os.startfile(file_path)
    elif os.name == 'posix':
        subprocess.call(('xdg-open', file_path))
    else:
        raise NotImplementedError('OS not supported: {}'.format(os.name))


def get_permission(filepath):
    """
    Returns the current permission level
    :param filepath: str
    """

    if os.access(filepath, os.R_OK | os.W_OK | os.X_OK):
        return True

    try:
        os.chmod(filepath, 0o775)
        return True
    except Exception:
        return False


def delete_file(file_path):
    """
    Delete the file by name in the directory
    :param name: str, name of the file to delete
    :param directory: str, the directory where the file is stored
    :return: str, file path that was deleted
    """

    if not os.path.isfile(file_path):
        logger.warning('File "{}" was not deleted.'.format(file_path))
        return False

    try:
        get_permission(file_path)
    except Exception:
        pass

    try:
        os.remove(file_path)
    except Exception as exc:
        pass

    if os.path.isfile(file_path):
        return False

    return True


def delete_folder(folder_name, directory=None):
    """
    Deletes the folder by name in the given directory
    :param folder_name: str, name of the folder to delete
    :param directory: str, the directory path where the folder is stored
    :return: str, folder that was deleted with path
    """

    def delete_read_only_error(action, name, exc):
        """
        Helper to delete read only files
        """

        os.chmod(name, 0o777)
        action(name)

    full_path = folder_name
    if directory:
        full_path = clean_path(os.path.join(directory, folder_name))
    if not os.path.isdir(full_path):
        return None

    try:
        shutil.rmtree(full_path, onerror=delete_read_only_error)
    except Exception as exc:
        logger.warning('Could not remove folder "{}" | {}'.format(full_path, exc))

    return full_path


def debug_object_string(obj, msg):
    """
    Returns a debug string depending of the type of the object

    :param object obj: Python object
    :param str msg: message to log
    :return: debug string
    :rtype: str
    """

    if inspect.ismodule(obj):
        return '[%s module] :: %s' % (obj.__name__, msg)
    elif inspect.isclass(obj):
        return '[%s.%s class] :: %s' % (obj.__module__, obj.__name__, msg)
    elif inspect.ismethod(obj):
        return '[%s.%s.%s method] :: %s' % (obj.im_class.__module__, obj.im_class.__name__, obj.__name__, msg)
    elif inspect.isfunction(obj):
        return '[%s.%s function] :: %s' % (obj.__module__, obj.__name__, msg)


def import_module(module_path, name=None, skip_exceptions=False):
    """
    Imports the given module path. If the given module path is a dotted one, import lib will be used. Otherwise, it's
    expected that given module path is the absolute path to the source file. If name argument is not given, then the
    basename without the extension will be used

    :param module_path: str, module path. Can be a dotted path (tpDcc.libs.python.modules) or an absolute one
    :param name: str, name for the imported module which will be used if the module path is an absolute path
    :param skip_exceptions: bool, Whether or not exceptions should be arise if a module cannot be imported
    :return: ModuleObject, imported module object
    """

    if is_dotted_module_path(module_path) and not os.path.exists(module_path):
        try:
            return importlib.import_module(module_path)
        except ImportError as exc:
            if not skip_exceptions:
                logger.exception('Failed to load module: "{}" | {}'.format(module_path, exc))
            return None

    try:
        if os.path.exists(module_path):
            if not name:
                name = os.path.splitext(os.path.basename(module_path))[0]
            if name in sys.modules:
                return sys.modules[name]
        if os.path.isdir(module_path):
            module_path = clean_path(os.path.join(module_path, '__init__.py'))
            if not os.path.exists(module_path):
                raise ValueError('Cannot find module path: "{}"'.format(module_path))
        if is_python2():
            return imp.load_source(name, os.path.realpath(module_path))
        else:
            return SourceFileLoader(name, os.path.realpath(module_path)).load_module()
    except ImportError:
        logger.error('Failed to load module: "{}"'.format(module_path))
        return None


def iterate_modules(path, exclude=None):
    """
    Iterates all Python modules of the given path
    :param str path: folder path to iterate searching for Python modules
    :param list(str) exclude: list of files to exclude during the searching process
    :return: Iterator with all the found modules
    :rtype: iterator
    """

    if not exclude:
        exclude = list()

    _exclude = ['__init__.py', '__init__.pyc']
    for root, dirs, files in os.walk(path):
        if '__init__.py' not in files:
            continue
        for f in files:
            base_name = os.path.splitext(f)[0]
            if f not in _exclude and base_name not in exclude:
                module_path = clean_path(os.path.join(root, f))
                if f.endswith('.py') or f.endswith('.pyc'):
                    yield module_path


def iterate_module_members(module_to_iterate, predicate=None):
    """
    Iterates all the members of the given modules
    :param ModuleObject module_to_iterate: module object to iterate members of
    :param inspect.cass predicate: if given members will be restricted to given inspect class
    :return:
    :rtype: iterator
    """

    for mod in inspect.getmembers(module_to_iterate, predicate=predicate):
        yield mod


def is_dotted_module_path(module_path):
    """
    Returns whether given module path is a dotted one (tpDcc.libs.python.modules) or not
    :param str module_path:
    :return:
    :rtype: bool
    """

    return len(module_path.split('.')) >= 2


def convert_module_path_to_dotted_path(path):
    """
    Returns a dotted path relative to the given path
    :param str  path: str, Path to module we want to convert to dotted path (eg. myPlugin/folder/test.py)
    :return: dotted path (eg. folder.test)
    :rtype: str
    """

    directory, file_path = os.path.split(path)
    directory = clean_path(directory)
    file_name = os.path.splitext(file_path)[0]
    package_path = [file_name]
    sys_path = [clean_path(p) for p in sys.path]
    drive_letter = os.path.splitdrive(path)[0] + '\\'
    while directory not in sys_path:
        directory, name = os.path.split(directory)
        directory = clean_path(directory)
        if directory == drive_letter or name == '':
            return ''
        package_path.append(name)

    return '.'.join(reversed(package_path))


def read_json(filename):
    """
    Get data from JSON file
    """

    if os.stat(filename).st_size == 0:
        return None
    else:
        try:
            with open(filename, 'r') as json_file:
                data = json.load(json_file)
        except Exception as err:
            logger.warning('Could not read {0}'.format(filename))
            raise err

    return data


def get_percent(value, minimum, maximum):
    if minimum == maximum:
        return 100
    return max(0, min(100, (value - minimum) * 100 / (maximum - minimum)))


def timestamp(f):
    """
    Function decorator that gets the elapsed time with a more descriptive output

    :param f: fn, function
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        res = f(*args, **kwargs)
        func_name = f.func_name if is_python2() else f.__name__
        logger.info('<{}> Elapsed time : {}'.format(func_name, time.time() - start_time))
        return res
    return wrapper


def abstract(fn):
    """
    Decorator that indicates that decorated function should be override
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        msg = 'DCC Abstract function {} has not been overridden.'.format(fn)
        raise NotImplementedError(debug_object_string(fn, msg))

    return wrapper


def add_metaclass(metaclass):
    """
    Decorators that allows to create a class using a metaclass
    https://github.com/benjaminp/six/blob/master/six.py
    :param metaclass:
    :return:
    """

    def wrapper(cls):
        orig_vars = cls.__dict__.copy()
        slots = orig_vars.get('__slots__')
        if slots is not None:
            if isinstance(slots, str):
                slots = [slots]
            for slots_var in slots:
                orig_vars.pop(slots_var)
        orig_vars.pop('__dict__', None)
        orig_vars.pop('__weakref__', None)
        if hasattr(cls, '__qualname__'):
            orig_vars['__qualname__'] = cls.__qualname__
        return metaclass(cls.__name__, cls.__bases__, orig_vars)
    return wrapper


class Singleton(object):
    """
    Implements Singleton pattern design as a class decorator in Python
    """

    all_instances = list()

    @staticmethod
    def destroy_all():
        for instance in Singleton.all_instances:
            instance.destroy()

    def __init__(self, cls):
        self.cls = cls
        self.instance = None
        self.all_instances.append(self)

    def destroy(self):
        del self.instance
        self.instance = None

    def __call__(self, *args, **kwargs):
        if self.instance is None:
            self.instance = self.cls(*args, **kwargs)

        return self.instance

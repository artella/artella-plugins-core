#!/usr/bin/env python
import base64
import hashlib
import json
import os
import random
import re
import socket
import threading
import time
import urllib
import urllib2
import urlparse

try:
    import maya.OpenMaya as OpenMaya
    import maya.OpenMayaMPx as OpenMayaMPx
    import maya.cmds
    import maya.mel
    import maya.utils
except Exception as e:
    print "maya libs not available... %s" % e

# Force stack trace on before we do any further imports
try:
    maya.mel.eval('stackTrace -state on')
    maya.cmds.optionVar(iv=('stackTraceIsOn', 1))
    whatIs = maya.mel.eval('whatIs "$gLastFocusedCommandReporter"')
    if whatIs != 'Unknown':
        gLastFocusedCommandReporter = maya.mel.eval(
            '$tmp = $gLastFocusedCommandReporter')
except Exception as e:
    print "error setting debug help... %s" % e


# -----------------------------------------------------------------------------
# Maya Setup
# -----------------------------------------------------------------------------
def initializePlugin(plugin):
    setup_menus()
    register_callbacks()

    plugin = OpenMayaMPx.MFnPlugin(plugin, "ArtellaForMaya", "0.0.1", "Any")
    register_commands(plugin)

    try:
        plugin.registerURIFileResolver(ArtSchemeResolver.kPluginResolverName,
                                       ArtSchemeResolver.kPluginURIScheme,
                                       ArtSchemeResolver.theCreator)
    except Exception as e:
        log_error("failed to register custom resolver: "
                  "%s for scheme: %s %s"
                  % (ArtSchemeResolver.kPluginResolverName,
                     ArtSchemeResolver.kPluginURIScheme, e))

    connect_to_artella_local_server()
    convert_paths_and_get_dependent_files()

    return


def setup_menus():
    gMainWindow = maya.mel.eval('$temp1=$gMainWindow')
    main_menu = maya.cmds.menu(
        "ArtellaMenu",
        parent=gMainWindow,
        label='Artella')

    maya.cmds.menuItem(
        'make_new_version',
        parent=main_menu,
        label=u'Save to Cloud',
        command=make_new_version,
        enable=True)

    maya.cmds.menuItem(
        'get_dependencies',
        parent=main_menu,
        label=u'Get Dependencies',
        command=get_dependencies,
        enable=True)

    maya.cmds.menuItem(
        'convert_file_paths',
        parent=main_menu,
        label=u'Convert file paths',
        command=convert_file_paths,
        enable=True)
    return


_callback_ids = {}


def register_callbacks():

    global _callback_ids

    id = OpenMaya.MSceneMessage.addCallback(
        OpenMaya.MSceneMessage.kBeforeSave,
        before_save)
    _callback_ids[OpenMaya.MSceneMessage.kBeforeSave] = id

    id = OpenMaya.MSceneMessage.addCallback(
        OpenMaya.MSceneMessage.kAfterOpen,
        after_open)
    _callback_ids[OpenMaya.MSceneMessage.kAfterOpen] = id

    id = OpenMaya.MSceneMessage.addCallback(
        OpenMaya.MSceneMessage.kAfterLoadReference,
        after_load_reference)
    _callback_ids[OpenMaya.MSceneMessage.kAfterLoadReference] = id

    id = OpenMaya.MSceneMessage.addCheckFileCallback(
        OpenMaya.MSceneMessage.kBeforeOpenCheck,
        before_open_check)
    _callback_ids[OpenMaya.MSceneMessage.kBeforeOpenCheck] = id

    id = OpenMaya.MSceneMessage.addCheckFileCallback(
        OpenMaya.MSceneMessage.kBeforeReferenceCheck,
        before_reference_check)
    _callback_ids[OpenMaya.MSceneMessage.kBeforeReferenceCheck] = id

    id = OpenMaya.MSceneMessage.addCheckFileCallback(
        OpenMaya.MSceneMessage.kBeforeCreateReferenceCheck,
        before_reference_check)
    _callback_ids[OpenMaya.MSceneMessage.kBeforeCreateReferenceCheck] = id

    return


def register_commands(plugin):

    for cmd in (ArtInfo, ArtGetDependencies, ArtPathConverter):
        try:
            plugin.registerCommand(cmd.name, cmd.creator)
        except Exception as e:
            log_error(
                "Failed to register command: %s" % cmd.name)
            raise e
    return


def connect_to_artella_local_server():
    # NOTE: this spins off a thread,
    # so we may need something specific to kill it
    setup_workspace()
    get_client().ws_listen()
    log_info("listening on ArtellaApp websocket...\n")
    return


def convert_paths_and_get_dependent_files():
    convert_file_paths()

    global _asked_for_get_deps

    deps = dependent_files(unresolved=True)
    if len(deps) < 1:
        return
    go_get_deps = user_wants_to_get_deps(deps)
    if not _asked_for_get_deps and go_get_deps:
        get_dependencies()

    return


def setup_workspace():
    ws = get_client().get_local_root()
    maya.mel.eval('setProject "%s"' % ws.replace('\\', '\\\\'))
    maya.cmds.workspace(directory=ws)
    maya.cmds.workspace(fileRule=['sourceImages', ''])
    maya.cmds.workspace(fileRule=['scene', ''])
    maya.cmds.workspace(fileRule=['mayaAscii', ''])
    maya.cmds.workspace(fileRule=['mayaBinary', ''])


# -----------------------------------------------------------------------------
# Maya Teardown
# -----------------------------------------------------------------------------
def uninitializePlugin(maya_obj):

    deregister_callbacks()

    if maya.cmds.menu("ArtellaMenu", ex=True):
        maya.cmds.deleteUI("ArtellaMenu")

    plugin = OpenMayaMPx.MFnPlugin(maya_obj)
    deregister_commands(plugin)
    try:
        plugin.deregisterURIFileResolver(
            ArtSchemeResolver.kPluginResolverName)
    except Exception as e:
        log_error("failed to deregister custom file resolver: %s %s"
                  % ArtSchemeResolver.kPluginResolverName, e)
    return


def deregister_callbacks():

    global _callback_ids

    for key in _callback_ids:
        OpenMaya.MMessage.removeCallback(_callback_ids[key])

    return


def deregister_commands(plugin):
    for cmd in (ArtInfo, ArtGetDependencies, ArtPathConverter):
        try:
            plugin.deregisterCommand(cmd.name)
        except Exception as e:
            log_error(
                "Failed to deregister command: %s" % cmd.name)
            raise e
    return

# -----------------------------------------------------------------------------
# Maya Callbacks
# -----------------------------------------------------------------------------


def before_save(*args):
    """ The 'BeforeSave' callback for Maya scenes.
    """
    validate_env_for_callback("BeforeSave")

    checked_out = checkout_file_if_necessary()
    if not checked_out:
        log_error("unable to checkout file to make new version")
        return

    # convert paths to remote scheme
    convert_file_paths()
    return


def before_reference_check(retcode, maya_file_obj, client_data=None):
    validate_env_for_callback("BeforeReferenceCheck")
    return


_current_file = None


def before_open_check(retcode, mfile, client_data=None):
    """ The 'BeforeOpenCheck' callback for Maya scenes.
    """
    validate_env_for_callback("BeforeOpenCheck")
    global _current_file
    global _asked_for_get_deps

    OpenMaya.MScriptUtil.setBool(retcode, True)

    # Cache the file being currently opened, which isn't accessible via
    # cmds.file(sceneName=True) until the load completes.
    _current_file = mfile.resolvedFullName()
    log_info('current file: %s' % _current_file)
    return


_asked_for_get_deps = False


def after_open(*args):
    validate_env_for_callback("AfterOpen")
    return


def after_load_reference(*args):
    validate_env_for_callback("AfterLoadReference")
    return


ALR = "ARTELLA_FOLDER_ROOT"


def validate_env_for_callback(callback_name):
    """ Check that all the necessary parts are available before executing
        the guts of a Maya callback method.
    """
    log_info("validate_env_for_callback for %s" % callback_name)
    local_root = get_client().get_local_root()
    if local_root is not None:
        # trying everything here to be safe
        # note that all docs say this only affects child processes of the main
        # this means that most of the time the env var needs to be set at
        # maya startup time via the Maya.env file or OS env
        #
        os.environ[ALR] = local_root
        os.putenv(ALR, local_root)
        maya.mel.eval('putenv "%s" "%s"' % (ALR, local_root))

    if ALR not in os.environ:
        msg = ("Unable to execute Maya '%s' callback, %s is not "
               "set in the environment." % (callback_name, ALR))
        log_error(msg)
        raise Exception(msg)

    return


# -----------------------------------------------------------------------------
# Realtime interactions
# -----------------------------------------------------------------------------
def pass_msg_to_maya(json_data):
    maya.utils.executeInMainThreadWithResult(
        handle_realtime_message, json_data)

    return


def handle_realtime_message(msg):

    if not isinstance(msg, dict):
        log_warning("malformed realtime message: %s" % msg)
        return

    command_name = msg.get('type')

    if command_name == 'maya-open':
        _realtime_open(msg)
    elif command_name == 'maya-import':
        _realtime_import(msg)
    elif command_name == 'maya-reference':
        _realtime_reference(msg)
    elif command_name == 'authorization-ok':
        log_info("websocket connection successful")
    elif command_name == 'progress-summary':
        pass
    elif command_name == 'transfer-status-change':
        pass
    else:
        log_warning("unknown command on websocket: %s" % command_name)


def _realtime_open(msg):
    args = msg['data']
    maya_file = args['ARTELLA_FILE']
    scenefile_type = maya.cmds.file(q=True, type=True)
    if isinstance(scenefile_type, list):
        scenefile_type = scenefile_type[0]
    filepath = maya_file.replace('\\', '/')
    maya.mel.eval('$filepath = "{}";'.format(filepath))
    maya.mel.eval('addRecentFile $filepath "{}";'.format(scenefile_type))


def _realtime_import(msg):
    args = msg['data']
    path = args['ARTELLA_FILE']
    maya.cmds.file(path, i=True, preserveReferences=True)


def _realtime_reference(msg):
    args = msg['data']
    path = args['ARTELLA_FILE']
    use_rename = maya.cmds.optionVar(q='referenceOptionsUseRenamePrefix')
    if use_rename:
        namespace = maya.cmds.optionVar(q='referenceOptionsRenamePrefix')
        maya.cmds.file(path, reference=True, namespace=namespace)
    else:
        filename = os.path.basename(path)
        namespace, _ = os.path.splitext(filename)
        maya.cmds.file(path, reference=True, namespace=namespace)


# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
def log_error(msg):
    print "!Artella ERROR: %s" % msg


def log_info(msg):
    print "Artella INFO: %s" % msg


def log_warning(msg):
    print "Artella WARNING: %s" % msg


DEBUG = False


def log_debug(msg):
    if DEBUG:
        print "Artella DEBUG %s" % msg


# -----------------------------------------------------------------------------
# Process Scene
# -----------------------------------------------------------------------------
def dependent_files(unresolved=False):
    fs = set()
    try:
        maya.cmds.filePathEditor(refresh=True)
        dirs = maya.cmds.filePathEditor(query=True, listDirectories="")
    except Exception as e:
        log_error("querying scene directories "
                  "looking for dependent files: %s" % e)
        return list()
    if not dirs:
        log_debug("file dirs not found")
        return list()
    for dir_name in dirs:
        try:
            files = maya.cmds.filePathEditor(query=True,
                                             listFiles=dir_name,
                                             unresolved=unresolved)
        except Exception as e:
            log_error("querying scene files in dir %s "
                      "looking for dependent files: %s" % (dir_name, e))
            continue
        if not files:
            # no files found in dir
            continue
        for file_name in files:
            log_debug("%s found needed file %s" % (dir_name, file_name))
            if is_already_uri_path(dir_name):
                fs.add("%s/%s" % (dir_name, file_name))
            else:
                fs.add(os.path.join(dir_name, file_name))
    return list(fs)


def convert_file_paths(maya_obj=None):
    try:
        maya.cmds.filePathEditor(refresh=True)
        dirs = maya.cmds.filePathEditor(query=True, listDirectories="")
    except Exception as e:
        log_error("querying scene directories "
                  "looking for dependent files: %s" % e)
        return
    if not dirs:
        log_debug("file dirs not found")
        return
    for dir_name in dirs:
        try:
            fpqr = maya.cmds.filePathEditor(query=True,
                                            listFiles=dir_name,
                                            withAttribute=True)
        except Exception as e:
            log_error("querying scene files in dir %s "
                      "looking for dependent files: %s" % (dir_name, e))
            return
        if not fpqr:
            continue
        i = 0
        while i < len(fpqr):
            """ rsp is expected to look like:
                [u"file1.ext", u"node1.attr", u"file2.ext", u"node2.attr", ...]
            """
            file_name = fpqr[i]
            node_attr_name = fpqr[i + 1]
            i += 2

            if is_already_uri_path(dir_name):
                log_debug(
                    "is already uri, skip: %s/%s" %
                    (dir_name, file_name))
                continue

            maya_dir = os.path.abspath(
                os.path.expandvars(
                    os.path.expanduser(dir_name)))

            log_debug("evaluating dir %s" % maya_dir)

            uri_dir = local_path_to_uri(maya_dir)
            if maya_dir == uri_dir:
                log_warning("unable to translate maya dir "
                            "to uri: %s" % maya_dir)
                continue

            uri = "%s/%s" % (uri_dir, file_name)

            if is_ref(node_attr_name):
                update_maya_reference_path(node_attr_name, uri)
                continue

            if '.' not in node_attr_name:
                log_warning("unable to identify attribute of %s "
                            "for file value %s" % (node_attr_name, uri))
                continue

            try:
                ga_rsp = maya.cmds.getAttr(node_attr_name, sl=True)
            except Exception as e:
                log_warning(
                    "unable to query attributes for %s" %
                    node_attr_name)
                continue

            if isinstance(ga_rsp, list):
                log_warning("not expecting a list for %s" % node_attr_name)
                for av in ga_rsp:
                    update_maya_attribute(node_attr_name, uri, av)
            else:
                update_maya_attribute(node_attr_name, uri, ga_rsp)

    return


def update_maya_attribute(node_attr_name, uri, current_value):
    if uri == current_value:
        # already set
        log_debug("%s already set to uri value %s" % (node_attr_name, uri))
        return
    node_name = node_attr_name.split('.')[0]

    if is_ref(node_name):
        update_maya_reference_path(node_name, uri)
    else:
        try:
            maya.cmds.setAttr(node_attr_name, uri, type='string')
        except Exception as e:
            log_warning("encountered an error while "
                        "attempting to modify an attribute "
                        "value %s: %s" % (node_attr_name, e))
        log_debug("setAttr %s %s" % (node_attr_name, uri))
        try:
            ga_rsp = maya.cmds.getAttr(node_attr_name, sl=True)
        except Exception as e:
            log_warning(
                "unable to query attributes for %s" %
                node_attr_name)
        if ga_rsp != uri:
            log_error("attempted %s update was not successful for %s "
                      "current value is %s" % (node_attr_name, uri, ga_rsp))
    return


def is_ref(node_attr_name):
    node_name = node_attr_name.split('.')[0]
    try:
        ir = maya.cmds.nodeType(node_name) == "reference"
    except RuntimeError as e:
        # Certain ref nodes throw errors
        log_warning("unable to query reference node %s: %s" % (node_name, e))
        ir = False
    return ir


def update_maya_reference_path(node_name, uri):
    node_name = node_name.split('.')[0]
    try:
        is_loaded = maya.cmds.referenceQuery(node_name, isLoaded=True)
    except Exception as e:
        log_warning("encountered an error while attempting to query "
                    "reference node %s %s" % (node_name, e))
    # https://help.autodesk.com/cloudhelp/2019/ENU/Maya-Tech-Docs/CommandsPython/referenceEdit.html#hExamples
    # So far, actually loading the file is the only way I've
    # found to change the reference path, but it seems like
    # there should be an attribute to poke
    if is_loaded:
        try:
            maya.cmds.file(unloadReference=node_name)
        except RuntimeError as e:
            log_error("encountered a Runtime error "
                      "while attempting to unload "
                      "reference file %s: %s" % (node_name, e))
    try:
        maya.cmds.file(uri, loadReference=node_name)
    except RuntimeError as e:
        log_error("encountered an error while attempting "
                  "to load the ref file using the updated "
                  "uri path %s: %s" % (uri, e))
    return


# -----------------------------------------------------------------------------
# Save to remote
# -----------------------------------------------------------------------------
def make_new_version(obj):

    file_ = maya.cmds.file(query=True, sceneName=True)
    if not file_:
        msg = "Unable to get file name, has it been created?"
        log_error(msg)
        maya.cmds.warning(msg)
        maya.cmds.confirmDialog(title="Artella Failed to make new version",
                                message=msg, button=["OK"])
        return

    checked_out = checkout_file_if_necessary()
    if not checked_out:
        log_error("unable to checkout file to make new version")
        return

    maya.cmds.file(save=True)

    result = maya.cmds.promptDialog(
        title="Artella Save to Cloud",
        message="Saving %s\n\nComment:" % os.path.basename(file_),
        button=["Save", "Cancel"],
        cancelButton="Cancel",
        dismissString="Cancel",
        scrollableField=True)

    if result == "Save":
        comment = maya.cmds.promptDialog(query=True, text=True)
        cms_uri = local_path_to_uri(file_)
        rsp = get_client().upload(cms_uri, comment)
        if rsp.get('error'):
            msg = "Unable to checkin file %s\n%s\n%s" % (
                os.path.basename(file_),
                rsp.get('url'),
                rsp.get('error'))
            maya.cmds.confirmDialog(
                title="Artella Failed to make new version",
                message=msg, button=["OK"])
            return False
    else:
        return False
    return True


def checkout_file_if_necessary(force=False):
    file_ = maya.cmds.file(query=True, sceneName=True)
    if not file_:
        return False

    if is_published(file_):
        msg = "Current file (%s) is published " \
            "and cannot be edited" % os.path.basename(file_)
        maya.cmds.confirmDialog(title="Artella Cannot Edit File",
                                message=msg,
                                button=["OK"])
        return False

    in_edit_mode, is_locked_by_me = is_locked_file(file_)
    can_write = os.access(file_, os.W_OK)
    if not can_write and is_locked_by_me:
        log_warning("unable to determin local write permissions for file: %s"
                    % file_)
    if in_edit_mode and not is_locked_by_me:
        msg = "This file is locked by another user or workspace.\n" \
              "Check the Artella Files Area for more info."

        maya.cmds.warning(msg)
        maya.cmds.confirmDialog(title="Artella Failed to checkout file",
                                message=msg,
                                button=["OK"])
        return False

    elif force or not in_edit_mode:
        result = "Yes"
        if not force and not in_edit_mode:
            msg = "%s needs to be in Edit Mode to save your file - " \
                "would you like to turn edit mode on now?" \
                % os.path.basename(file_)
            result = maya.cmds.confirmDialog(
                title="Artella Edit Mode",
                message=msg,
                button=["Yes", "No"],
                cancelButton="No",
                dismissString="No")

        if result != "Yes":
            return False

        if is_already_uri_path(file_):
            cms_uri = file_
        else:
            cms_uri = local_path_to_uri(file_)

        uri_parts = urlparse.urlparse(cms_uri)
        if not get_client().checkout_file(uri_parts.path):
            msg = "Failed to lock %s" % os.path.basename(file_)
            maya.cmds.warning(msg)
            maya.cmds.confirmDialog(title="Artella Failed to Lock file",
                                    message=msg,
                                    button=["OK"])
            return False

    return True


def unlock_file(maya_path):
    msg = "you have this file locked in Artella.\nUnlock it now?"
    result = maya.cmds.confirmDialog(
        title="Artella file is locked",
        message=msg,
        button=["Yes", "No"],
        cancelButton="No",
        dismissString="No")

    if result != "Yes":
        return

    if is_already_uri_path:
        cms_uri = maya_path
    else:
        cms_uri = local_path_to_uri(maya_path)

    uri_parts = urlparse.urlparse(cms_uri)
    if not get_client().unlock_file(uri_parts.path):
        msg = "Failed to unlock the file.\nTry unlocking it "\
              "from the Artella Files Area in the web browser."
        maya.cmds.warning(msg)
        maya.cmds.confirmDialog(title="Artella Failed to Lock file",
                                message=msg,
                                button=["OK"])
    return


def is_locked_file(maya_path):
    """ Return whether an absolute file path refers to a locked
        asset in edit mode, and if the file is locked by the
        current storage worksapce.
    """
    if not is_already_uri_path(maya_path):
        maya_path = local_path_to_uri(maya_path)
    rsp = get_status(maya_path)

    locked_machine_id = rsp.get('machine_id')

    raw = rsp.get('raw')
    if not raw:
        log_error("unable to get remote details for file %s" % maya_path)
        return False, False

    locked_by = raw.get('locked_by')
    if locked_by and locked_machine_id:
        storage_id = get_client().get_storage_id()
        return True, storage_id == locked_machine_id
    return False, False


def is_published(maya_path):
    """ Get the file status and parse the client status response object and return
        whether the the file is published.
    """
    return get_status(maya_path).get('published', False)


def get_status(maya_path):
    if not is_already_uri_path(maya_path):
        maya_path = local_path_to_uri(maya_path)
    rsp = get_client().status(maya_path)
    log_debug("status response: %s" % rsp)
    return rsp


# -----------------------------------------------------------------------------
# Get Dependencies
# -----------------------------------------------------------------------------
def user_wants_to_get_deps(deps):
    if len(deps) > 10:
        deps = deps[:10]
        deps.append('...')
    title = 'Artella - Missing dependency'
    msg = ('One or more dependent files are missing.\n'
           'Would you like to download all missing files?\n\n  %s'
           ) % "\n  ".join(deps)
    result = maya.cmds.confirmDialog(title=title,
                                     message=msg,
                                     button=["Yes", "No"],
                                     cancelButton="No",
                                     dismissString="No")
    return result == "Yes"


def get_dependencies(maya_obj=None):
    """ iterate over the maya scene graph and recursively process file paths
        to ensure that all necessary files have been sync'd to the local
        filesystem.  present feedback to the user.
    """
    deps_to_get = dependent_files(unresolved=True)
    if len(deps_to_get) < 1:
        log_info("did not find any dependencies needed.")
        return
    maya.cmds.progressWindow(
        title="Get Dependencies",
        progress=0,
        status="Evaluating scene for dependent files",
        isInterruptable=True
    )
    get_client().download(deps_to_get)
    time.sleep(0.25)
    while True:
        if maya.cmds.progressWindow(query=True, isCancelled=True):
            # stop downloads
            get_client().pause_downloads()
            break

        progress, fd, ft, bd, bt = get_client().get_progress()
        maya.cmds.progressWindow(
            edit=True,
            progress=progress,
            status="%d of %d KiB downloaded\n%d of %d files downloaded"
            % (int(bd / 1024), int(bt / 1024), fd, ft)
        )
        maya.cmds.refresh()

        if progress >= 100 or bd == bt:
            break

    maya.cmds.progressWindow(endProgress=1)
    return


class ArtGetDependencies(OpenMayaMPx.MPxCommand):
    name = "artGetDependencies"

    def __init__(self):
        OpenMayaMPx.MPxCommand.__init__(self)

    @staticmethod
    def creator():
        return OpenMayaMPx.asMPxPtr(ArtGetDependencies())

    def doIt(self, args):
        log_info("getting dependencies for scene file and translate paths")
        rsp = get_dependencies()
        log_info(rsp)


# -----------------------------------------------------------------------------
# Artella path converter
# -----------------------------------------------------------------------------
class ArtPathConverter(OpenMayaMPx.MPxCommand):
    name = "artConvertPaths"

    def __init__(self):
        OpenMayaMPx.MPxCommand.__init__(self)

    @staticmethod
    def creator():
        return OpenMayaMPx.asMPxPtr(ArtPathConverter())

    def doIt(self, args):
        log_info("convert file paths to artella uri scheme...")
        convert_file_paths()


# -----------------------------------------------------------------------------
# Artella Info
# -----------------------------------------------------------------------------
class ArtInfo(OpenMayaMPx.MPxCommand):
    name = "artInfo"

    def __init__(self):
        OpenMayaMPx.MPxCommand.__init__(self)

    @staticmethod
    def creator():
        return OpenMayaMPx.asMPxPtr(ArtInfo())

    def doIt(self, args):
        log_info("Plugin Status Info...")
        cli = get_client()
        print cli.get_metadata()
        print cli.get_storage_id()
        print cli.ping()
        print cli.ws_connect()
        ws = cli.get_local_root()
        print "local root %s" % ws


# -----------------------------------------------------------------------------
# File Resolver
# -----------------------------------------------------------------------------
def uri_to_local_path(uri_string):
    rsp = get_client().resolve(uri_string)
    if 'error' in rsp:
        log_warning("unable to translate path %s %s"
                    % (uri_string, rsp.get('error')))
        return uri_string
    return rsp.get('file_path')


def is_already_uri_path(maya_path, prefix=None):
    if not maya_path:
        return False
    if prefix:
        log_warning("prefix support not implemented yet")

    uri = urlparse.urlparse(maya_path)
    return uri.scheme == ArtSchemeResolver.kPluginURIScheme


def local_path_to_uri(maya_path, prefix=None, preserve_maya_fmt=False):
    if prefix:
        # TODO: handle TCL based path strings for Pixar nodes
        log_warning("not implemented yet support for TCL")

    elp = os.path.abspath(os.path.expandvars(os.path.expanduser(maya_path)))
    rsp = get_client().resolve(elp)
    if 'error' in rsp:
        log_warning("unable to translate path %s %s"
                    % (maya_path, rsp.get('error')))
        return maya_path

    url_parts = (
        ArtSchemeResolver.kPluginURIScheme,
        '',
        rsp.get('handle'),
        '',
        '',
        '')
    # 'artella:path/to/file.ext'
    fixed_path = urlparse.urlunparse(url_parts)
    if not is_already_uri_path(fixed_path):
        log_error("failed to translate %s to uri: %s"
                  % (maya_path, fixed_path))
        return maya_path
    return fixed_path


def might_be_a_file_path(maya_path):

    pathPatterns = (
        re.compile(r'(\$%s[\\/\w\.<>#\s-]+)' % ALR),
        re.compile(r'(\.\.[\\/\w\.<>#\s-]+)'),
        re.compile(r'((\w\:)|(/))[\\/\w\.<>#-]+[\\/][\\/\w\.<>#-]+'),
        re.compile(r'((\w\:)|(/))[\\/\w\.<>#\s-]+[\\/][\\/\w\.<>#\s-]+')
    )

    if not maya_path:
        return False

    for prog in pathPatterns:
        is_match = prog.match(maya_path)
        if is_match:
            log_info("found file path %s: %s %s" % (
                is_match.string,
                prog.pattern,
                is_match.groups()))
            return True
    return False


class ArtSchemeResolver(OpenMayaMPx.MPxFileResolver):
    """ This custom plug-in resolver handles the 'artella' uri scheme.
        This resolver will check that the file has been downloaded
        from the Artella remote server and is in place on the local
        file system.
    """

    kPluginURIScheme = "artella"
    kPluginResolverName = "ArtSchemeResolver"

    def __init__(self):
        OpenMayaMPx.MPxFileResolver.__init__(self)
        self._workspace = None

    def uriScheme(self):
        return (self.kPluginURIScheme)

    def resolveURI(self, URI, mode):
        log_debug("resolver URI: %s" % URI.asString())
        local_path = uri_to_local_path(URI.asString())
        log_debug("resolver local_path: %s" % local_path)
        return local_path

    def performAfterSaveURI(self, URI, resolvedFullPath):
        uri = URI.asString()
        log_info("push to cloud: %s" % resolvedFullPath, uri)

    @staticmethod
    def theCreator():
        return OpenMayaMPx.asMPxPtr(ArtSchemeResolver())

    @staticmethod
    def className():
        return "ArtSchemeResolver"


# -------------------------------------------------------------------
# ArtellaApp connection client
# -------------------------------------------------------------------
DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 29282
CRLF = "\r\n"


_cli = None

_auth_header = "artella-file-challenge artella-challenge {}"
_challenge_path = None


def get_client():
    # is there value is reusing this?
    global _cli
    if _cli is None:
        _cli = ArtellaAppClient()
    # challenge value gets updated when the Artella App restarts
    # need to check this each time in case it restarted but Maya didnt
    _cli.auth_challenge_update()
    return _cli


def make_ws_key():
    # https://tools.ietf.org/html/rfc6455
    key = base64.b64encode(str(int(random.random() * 9999999)))
    h = hashlib.sha1()
    h.update(key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11")
    expected_key_response = base64.b64encode(h.digest())
    return key, expected_key_response


class SocketBuffer(object):
    def __init__(self, sock):
        super(SocketBuffer, self).__init__()
        self.sock = sock
        self.buf = ""

    def read_line(self):
        line = ""
        while True:
            c = self.get_char()
            line += c
            if c == "\n":
                return line

    def get_char(self):
        if len(self.buf) == 0:
            self.buf = self.sock.recv(2000)
        r = self.buf[0]
        self.buf = self.buf[1:]
        return r

    def get_chars(self, count):
        cc = ""
        for x in xrange(0, count):
            cc += self.get_char()
        return cc


_resolver_cache = {}


class ArtellaAppClient():

    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        self._host = host
        self._port = port
        self._auth_header = None
        self._batch_ids = set()
        self._socket_buffer = None

    def auth_challenge_update(self):
        """ collect some data from a local file to confirm we are running
            on the same machine that the Artella app is running.
        """
        global _challenge_path
        if not _challenge_path:
            rsp = self.get_challenge_file_path()
            if not rsp:
                log_error("unable to get challenge file path %s" % rsp)
                self._auth_header = None
                return self._auth_header
            _challenge_path = rsp.get("challenge_file_path")
        if not os.path.exists(_challenge_path):
            log_error("challenge file not found %s" % _challenge_path)
            self._auth_header = None
            return self._auth_header
        with open(os.path.expanduser(_challenge_path)) as fp:
            b = fp.read()
        self._auth_header = _auth_header.format(b[:64].encode("hex"))
        return self._auth_header

    def ws_connect(self):
        server_address = (self._host, self._port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        log_info("connecting to Artella App websocket: %s:%s"
                 % server_address)
        try:
            sock.connect(server_address)
        except Exception as e:
            log_error("plugin failed to connect to the "
                      "App websocket: %s" % e)
            return

        self.ws_send_request(sock)
        self._socket_buffer = SocketBuffer(sock)
        rsp = self.ws_read_response()
        return rsp

    def ws_send_request(self, sock):
        key, expected_key_response = make_ws_key()
        if not self.auth_challenge_update():
            log_error("unable to authenticate")
            return
        path = "/v2/localserve/ws"
        r = [
            "GET {} HTTP/1.1".format(path),
            "Upgrade: websocket",
            "Connection: Upgrade",
            "Host: {}:{}".format(self._host, self._port),
            "Sec-WebSocket-Key: {}".format(key),
            "Sec-WebSocket-Version: 13",
            "Authorization: {}".format(self._auth_header),
        ]
        rr = CRLF.join(r) + CRLF + CRLF
        log_debug("plugin sending websocket access request to "
                  " the local ArtellaApp: %s" % rr)
        sock.sendall(rr)

    def ws_read_response(self):
        log_debug("reading socket response...")
        line = ""
        while line != CRLF:
            line = self._socket_buffer.read_line()
        return line

    def ws_listen(self):
        self.ws_connect()
        if not self._socket_buffer:
            log_error("socket not connected")
            return
        threading.Thread(
            target=self._pull_messages,
        ).start()

    def _pull_messages(self):
        log_info("listening for commands on websocket")
        while True:
            msg = self._get_message()
            pass_msg_to_maya(msg)

    def _get_message(self):
        opcode = ord(self._socket_buffer.get_char())
        v = ord(self._socket_buffer.get_char())
        if opcode != 129:
            raise Exception("not a final text frame :" + str(opcode))
        if v < 126:
            length = v
        elif v == 126:
            a = ord(self._socket_buffer.get_char()) << 8
            b = ord(self._socket_buffer.get_char())
            length = a + b
        elif v == 127:
            # 8 byte payload length - we won't have any of these
            raise Exception("unsuported payload length")
        else:
            raise Exception("bad payload length: " + str(v))

        payload = self._socket_buffer.get_chars(length)

        return json.loads(payload)

    def ping(self):
        req = urllib2.Request(
            "http://%s:%s/v2/localserve/ping" %
            (self._host, self._port))
        rsp = self._communicate(req)
        return rsp

    def get_challenge_file_path(self):
        req = urllib2.Request(
            "http://%s:%s/v2/localserve/auth/challenge-file-path" %
            (self._host, self._port))
        rsp = self._communicate(req, skip_auth=True)
        return rsp

    def get_local_root(self):
        """ ask the remote server for the local storage root for this machine
        """
        req = urllib2.Request(
            "http://%s:%s/v2/localserve/kv/settings/workspace" %
            (self._host, self._port))
        ws = self._communicate(req)
        if not ws:
            alr = os.environ.get(ALR, None)
            if alr:
                log_warning("unable to get local storage root "
                            "using env var: %s" % ALR)
                ws = alr
            else:
                log_error("unable to get local storage root")
                log_info("check that the local Artella Studio service is "
                         "running and you have a working internet connection")
                log_info("to work offline set the %s environment variable "
                         "to the appropriate local project directory." % ALR)
        return ws

    def get_storage_id(self):
        """ ask for the storage id of the machine this code is running on
        """
        req = urllib2.Request(
            "http://%s:%s/v2/localserve/kv/settings/machine-id" %
            (self._host, self._port))
        rsp = self._communicate(req)
        return rsp

    def get_metadata(self):
        """ ask the remote server for general data related to current session
        """
        params = urllib.urlencode({'dump': 'true'})
        req = urllib2.Request(
            "http://%s:%s/v2/localserve/kv/settings?%s" %
            (self._host, self._port, params))
        rsp = self._communicate(req)
        return rsp

    def resolve(self, path):
        global _resolver_cache
        cached = _resolver_cache.get(path)
        if cached:
            return cached
        if is_already_uri_path(path):
            payload = {'handle': path}
        else:
            payload = {'file_path': path}
        req = urllib2.Request(
            "http://%s:%s/v2/localserve/resolve" %
            (self._host, self._port))
        req.add_header('Content-Type', 'application/json')
        rsp = self._communicate(req, json.dumps(payload))
        if 'error' in rsp:
            log_error("attempting to resolve %s %s"
                      % (path, rsp.get('error')))
        _resolver_cache[path] = rsp
        return rsp

    def download(self, artella_uri_list):
        """ pull the file from the remote server
        """
        handles = set()
        for uri in artella_uri_list:
            if not is_already_uri_path(uri):
                uri = local_path_to_uri(uri)
            uri_parts = urlparse.urlparse(uri)
            handle = uri_parts.path
            handles.add(handle)

        if not handles:
            return {}
        log_debug("  handles %s" % handles)
        payload = {
            'handles': list(handles),
            'recursive': False,
            'replace_local': True
        }
        log_debug("   request payload orig: %s" % payload)
        req = urllib2.Request(
            "http://%s:%s/v2/localserve/transfer/download" %
            (self._host, self._port))
        req.add_header('Content-Type', 'application/json')
        rsp = self._communicate(req, json.dumps(payload))
        if 'error' in rsp:
            return rsp
        return self.track_response(rsp)

    def upload(self, artella_uri, comment=""):
        """ upload an updated file to the remote server
        """
        uri_parts = urlparse.urlparse(artella_uri)
        handle = uri_parts.path
        payload = {
            'handles': [handle],
            'recursive': False,
            'commit_message': comment
        }
        req = urllib2.Request(
            "http://%s:%s/v2/localserve/transfer/upload" %
            (self._host, self._port))
        req.add_header('Content-Type', 'application/json')
        rsp = self._communicate(req, json.dumps(payload))
        if 'error' in rsp:
            return rsp
        return self.track_response(rsp)

    def checkout_file(self, artella_uri):
        """ lock it
        """
        payload = {
            'handle': artella_uri,
            'note': 'Artella for Maya checkout'
        }
        req = urllib2.Request(
            "http://%s:%s/v2/localserve/lock" %
            (self._host, self._port))
        req.add_header('Content-Type', 'application/json')
        rsp = self._communicate(req, json.dumps(payload))
        if 'error' in rsp:
            log_error(rsp.get('error'))
            return False

        return rsp.get('response', False) and rsp.get('status_code', 0) == 200

    def unlock_file(self, artella_uri):
        """ unlock it
        """
        payload = {
            'handle': artella_uri
        }
        req = urllib2.Request(
            "http://%s:%s/v2/localserve/unlock" %
            (self._host, self._port))
        req.add_header('Content-Type', 'application/json')
        rsp = self._communicate(req, json.dumps(payload))
        if 'error' in rsp:
            log_error(rsp.get('error'))
            return False

        return rsp.get('response', False) and rsp.get('status_code', 0) == 200

    def status(self, artella_uri):
        """ get the status of a file from the remote server
        """
        uri_parts = urlparse.urlparse(artella_uri)
        params = urllib.urlencode({'handle': uri_parts.path})
        req = urllib2.Request(
            "http://%s:%s/v2/localserve/fileinfo?%s" %
            (self._host, self._port, params))
        rsp = self._communicate(req)
        if 'error' in rsp:
            return rsp
        # TODO: once we have a reliable way to resolve the record handle
        # back into the abs path, iterate and match on the file name
        for k, v in rsp.iteritems():
            if os.path.basename(k) == os.path.basename(artella_uri):
                return v.get('remote_info', {})
        return rsp

    def get_progress(self):

        tx_count_done = 0
        tx_count_total = 0
        tx_bytes_done = 0
        tx_bytes_total = 0
        batches_complete = set()
        for batch_id in self._batch_ids:
            params = urllib.urlencode({
                'batch-id': batch_id,
                'details': True})
            req = urllib2.Request(
                "http://%s:%s/v2/localserve/progress/summary?%s" %
                (self._host, self._port, params))
            v = self._communicate(req)
            tcd = int(v.get('transfer_count_done', 0))
            tct = int(v.get('transfer_count_total', 0))
            tbd = int(v.get('transfer_bytes_download_done', 0))
            tbt = int(v.get('transfer_bytes_download_total', 0))
            if tcd == tct or tbd == tbt:
                batches_complete.add(batch_id)
                continue
            tx_count_done += tcd
            tx_count_total += tct
            tx_bytes_done += tbd
            tx_bytes_total += tbt

        self._batch_ids -= batches_complete

        progress_value = 1
        if tx_bytes_total > 0:
            progress_value = float(tx_bytes_done) / float(tx_bytes_total)
        elif tx_count_total > 0:
            progress_value = float(tx_count_done) / float(tx_count_total)

        return (
            int(progress_value * 100),
            tx_count_done,
            tx_count_total,
            tx_bytes_done,
            tx_bytes_total
        )

    def pause_downloads(self):
        req = urllib2.Request(
            "http://%s:%s/v2/localserve/pause/pause/downloads" %
            (self._host, self._port))
        rsp = self._communicate(req, {"noop": ""})
        return rsp

    def track_response(self, rsp):
        """ extrack batch_id and transfer data from response
            so that we can continue to track progress
        """
        batch_id = rsp.get('batch_id')
        self._batch_ids.add(batch_id)
        return rsp

    def _communicate(self, req, data=None, skip_auth=False):
        log_debug(">>> making request to ArtellaApp %s"
                  % req.get_full_url())
        if data:
            log_debug("  request payload dump: %s"
                      % json.loads(data))
        if not self._auth_header and not skip_auth:
            rsp = self.auth_challenge_update()
            if not rsp:
                msg = "unable to authenticate"
                log_error(msg)
                return {'error': msg,
                        'url': req.get_full_url()}

        req.add_header('Authorization', self._auth_header)

        try:
            rsp = urllib2.urlopen(req, data)
        except urllib2.URLError as e:
            if hasattr(e, 'reason'):
                msg = "failed to reach the local ArtellaApp: %s" \
                    % e.reason
            elif hasattr(e, 'code'):
                msg = "ArtellaApp is unable to fulfill the request: %s" \
                    % e.code
            log_debug(e)
            log_error(msg)
            return {'error': msg,
                    'url': req.get_full_url()}
        else:
            raw_data = rsp.read()
            try:
                json_data = json.loads(raw_data)
            except Exception as e:
                log_debug("  ArtellaApp data response: %s" % raw_data)
                return raw_data
            else:
                log_debug("  ArtellaApp JSON response: %s" % json_data)
                return json_data
